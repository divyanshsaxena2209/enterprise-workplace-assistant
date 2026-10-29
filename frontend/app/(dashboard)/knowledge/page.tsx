"use client";
import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { UploadCloud, MessageSquare, FileText, Database, Sparkles, Loader2, X, ExternalLink, Trash2 } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/context/UserContext";
import { uploadKnowledgeDocument, deleteKnowledgeDocument, getKnowledgeDocumentDownloadUrl, listKnowledgeDocuments } from "@/lib/api/knowledge";
import LockedFeature from "@/components/layout/LockedFeature";
export default function KnowledgeDashboard() {
  const { profile, isHired } = useUser();
  const [documents, setDocuments] = useState<any[]>([]);
  const [searchesRun, setSearchesRun] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [toastMessage, setToastMessage] = useState<{type: 'success'|'error', text: string} | null>(null);
  const [viewingDoc, setViewingDoc] = useState<{url: string, title: string} | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [uploadDepartmentScope, setUploadDepartmentScope] = useState("ALL");
  useEffect(() => {
    let cancelled = false;
    const savedSearches = parseInt(localStorage.getItem('knowledge_searches') || '0', 10);
    setSearchesRun(Number.isFinite(savedSearches) ? savedSearches : 0);

    let savedDocs: any[] = [];
    try {
      const parsed = JSON.parse(localStorage.getItem('knowledge_documents') || '[]');
      savedDocs = Array.isArray(parsed) ? parsed : [];
    } catch {
      savedDocs = [];
    }
    const isManagementProfile = ["MANAGEMENT", "ADMIN", "HR"].includes(profile?.role || "");
    // Browser localStorage is not a trusted source of access-scope metadata.
    // Employees initially see no legacy entries while the server registry loads.
    setDocuments(isManagementProfile ? savedDocs : []);

    // The API registry is the shared source of truth. Legacy local-only entries are
    // retained only for Management to review and re-upload into the server registry.
    async function loadRegisteredDocuments() {
      try {
        const result = await listKnowledgeDocuments();
        if (!Array.isArray(result)) return;
        const registered = result.map((doc: any) => ({
          id: String(doc.id),
          managed_by_api: true,
          title: doc.filename,
          uploaded: doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "",
          dept: doc.department_scope || "ALL",
          department_scope: doc.department_scope || "ALL",
          file_url: doc.file_url || undefined,
          file_key: doc.file_key,
          uploaded_by: doc.uploaded_by,
          storage_provider: doc.storage_provider,
          pages: doc.pages,
          chunks: doc.chunks,
        }));
        const registeredKeys = new Set(
          registered.map((doc: any) => doc.file_key ? `${doc.storage_provider}:${doc.file_key}` : ""),
        );
        const legacy = isManagementProfile
          ? savedDocs.filter((doc: any) => {
              const key = doc.file_key ? `${doc.storage_provider || "supabase"}:${doc.file_key}` : "";
              return !key || !registeredKeys.has(key);
            }).map((doc: any) => ({ ...doc, managed_by_api: false }))
          : [];
        const merged = [...registered, ...legacy];
        if (!cancelled) {
          setDocuments(merged);
          localStorage.setItem("knowledge_documents", JSON.stringify(merged));
        }
      } catch {
        // Never fall back to untrusted browser-local document entries for employees.
        if (!cancelled) setDocuments(isManagementProfile ? savedDocs : []);
      }
    }

    if (profile?.id) void loadRegisteredDocuments();
    return () => { cancelled = true; };
  }, [profile?.id, profile?.department, profile?.role]);
  const handleDeleteDocument = async (e: React.MouseEvent, docId: string, filename: string, file_url?: string, file_key?: string, storage_provider?: string, managedByApi?: boolean) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete "${filename}" from the Knowledge Base? This cannot be undone.`)) return;
    setIsDeleting(true);
    try {
      await deleteKnowledgeDocument(filename, file_url, file_key, storage_provider, managedByApi ? docId : undefined);
      await new Promise(resolve => setTimeout(resolve, 2000));
      const updatedDocs = documents.filter(doc => doc.id !== docId);
      setDocuments(updatedDocs);
      localStorage.setItem('knowledge_documents', JSON.stringify(updatedDocs));
      setToastMessage({ type: 'success', text: `Successfully deleted ${filename} from the Knowledge Base.` });
    } catch (error: any) {
      setToastMessage({ type: 'error', text: error.message || "Failed to delete document." });
    } finally {
      setIsDeleting(false);
    }
  };
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    const isDocx = file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" || file.name.toLowerCase().endsWith(".docx");
    if (!isPdf && !isDocx) {
      setToastMessage({ type: 'error', text: "Only PDF and DOCX files are supported." });
      return;
    }
    setIsUploading(true);
    setToastMessage(null);
    try {
      const result = await uploadKnowledgeDocument(file, uploadDepartmentScope);
      const newDoc = {
        id: String(result.id || Date.now()),
        managed_by_api: Boolean(result.id),
        uploaded_by: result.uploaded_by || profile?.id,
        title: result.filename || file.name,
        uploaded: result.created_at ? new Date(result.created_at).toLocaleDateString() : new Date().toLocaleDateString(),
        dept: result.department_scope || uploadDepartmentScope || "ALL",
        department_scope: result.department_scope || uploadDepartmentScope || "ALL",
        file_url: result.file_url || undefined,
        file_key: result.file_key,
        storage_provider: result.storage_provider,
        pages: result.pages,
        chunks: result.chunks
      };
      const updatedDocs = [newDoc, ...documents];
      setDocuments(updatedDocs);
      localStorage.setItem('knowledge_documents', JSON.stringify(updatedDocs));
      setToastMessage({ type: 'success', text: `Successfully indexed ${result.filename}.` });
    } catch (error: any) {
      setToastMessage({ type: 'error', text: error.message || "Failed to upload document." });
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };
  const getViewerUrl = (url: string) => {
    if (url.toLowerCase().endsWith('.docx') || url.toLowerCase().endsWith('.doc') || url.includes('.docx?') || url.includes('.doc?')) {
      return `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(url)}`;
    }
    return url;
  };
  return (
    <LockedFeature isLocked={!profile?.employee_id && !['MANAGEMENT', 'ADMIN', 'HR'].includes(profile?.role || '')}>
      <div className="space-y-8 pb-10">
      {toastMessage && (
        <div className={`p-4 rounded-lg text-sm font-semibold ${toastMessage.type === 'error' ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-green-500/10 text-green-500 border border-green-500/20'}`}>
          {toastMessage.text}
        </div>
      )}
      {}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            Knowledge Base
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Search and ask questions about your company documents.</p>
        </div>
        <div className="flex gap-3">
          {(profile?.employee_id || ["MANAGEMENT", "ADMIN", "HR"].includes(profile?.role || "")) && (
            <div className="flex items-center gap-2 flex-wrap">
              <input 
                type="file" 
                id="file-upload" 
                className="hidden" 
                accept=".pdf,.docx" 
                onChange={handleFileUpload}
                disabled={isUploading}
              />
              <label 
                htmlFor="file-upload"
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border border-border bg-secondary/50 text-xs font-bold uppercase tracking-wider cursor-pointer hover:bg-secondary transition-all shadow-sm ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
              >
                {isUploading ? <Loader2 size={14} className="animate-spin" /> : <UploadCloud size={14} />}
                {isUploading ? "Indexing..." : "Upload Document"}
              </label>
            </div>
          )}
          <Link 
            href="/knowledge/chat" 
            className="flex items-center gap-2 bg-transparent border border-white hover:bg-white/10 text-white px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all active:scale-95 cursor-pointer shadow-sm"
          >
            <MessageSquare size={14} />
            Ask Questions
          </Link>
        </div>
      </div>
      {}
      <div className="grid grid-cols-1 gap-6">
        <div className="p-6 bg-foreground rounded-2xl shadow-sm text-background flex flex-col justify-between h-40">
          <Database size={24} className="opacity-80" />
          <div>
            <h3 className="text-4xl font-black tracking-tight">{documents.length}</h3>
            <p className="text-background/80 font-bold text-[10px] uppercase tracking-wider mt-2">Documents Uploaded</p>
          </div>
        </div>
      </div>
      {}
      <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-border/50 flex justify-between items-center bg-secondary/50">
          <h3 className="font-bold text-xs uppercase tracking-wider text-foreground">Recent Documents</h3>
        </div>
        <div className="divide-y divide-border/50">
          {documents.map(doc => (
            <div 
              key={doc.id} 
              className={`p-5 flex items-center justify-between transition-colors group ${(doc.file_url || (doc.managed_by_api && doc.storage_provider && doc.file_key)) ? 'hover:bg-secondary/30 cursor-pointer' : ''}`}
              onClick={async () => {
                if (doc.managed_by_api && ["s3", "supabase"].includes(doc.storage_provider) && doc.file_key) {
                  try {
                    const result = await getKnowledgeDocumentDownloadUrl(doc.file_key);
                    if (!result?.file_url) throw new Error("No download URL was returned.");
                    setViewingDoc({ url: result.file_url, title: doc.title });
                  } catch (error: any) {
                    setToastMessage({ type: 'error', text: error.message || "Could not generate a secure download link." });
                  }
                } else if (doc.file_url) {
                  setViewingDoc({ url: doc.file_url, title: doc.title });
                } else {
                  setToastMessage({ type: 'error', text: 'This legacy document was not uploaded to storage and cannot be viewed.' });
                }
              }}
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg border border-border flex items-center justify-center bg-background text-muted-foreground group-hover:text-foreground transition-colors shadow-sm">
                  <FileText size={18} />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-foreground tracking-tight group-hover:underline">{doc.title}</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">Ingested {doc.uploaded}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {(
                  ["MANAGEMENT", "ADMIN", "HR"].includes(profile?.role || "") ||
                  (profile?.role === "EMPLOYEE" && Boolean(doc.managed_by_api) && String(doc.uploaded_by || "") === String(profile?.id || ""))
                ) && (
                  <button
                    type="button"
                    onClick={(e) => void handleDeleteDocument(
                      e,
                      String(doc.id),
                      doc.title,
                      doc.file_url,
                      doc.file_key,
                      doc.storage_provider,
                      Boolean(doc.managed_by_api),
                    )}
                    disabled={isDeleting}
                    aria-label={`Delete ${doc.title}`}
                    title="Delete document"
                    data-testid="delete-knowledge-document"
                    className="inline-flex min-w-[92px] flex-shrink-0 items-center justify-center gap-2 rounded-lg border border-red-500/50 bg-red-500/10 px-3 py-2 text-xs font-black uppercase tracking-wider text-red-400 opacity-100 transition-colors hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Trash2 size={14} />
                    <span>Delete</span>
                  </button>
                )}
              </div>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="p-8 text-center text-muted-foreground text-sm">
              No documents have been indexed yet.
            </div>
          )}
        </div>
      </div>
      </div>
      {}
      {(isUploading || isDeleting) && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/60 backdrop-blur-md">
          {isUploading && (
            <div className="flex flex-col items-center gap-4 animate-in fade-in duration-300">
              <div className="bg-green-500/10 p-6 rounded-full flex items-center justify-center">
                <svg className="w-16 h-16 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" style={{ strokeDasharray: 70, strokeDashoffset: 70, animation: 'draw-erase-loop 2s ease-in-out infinite' }} />
                  <path d="M14 2v4a2 2 0 0 0 2 2h4" style={{ strokeDasharray: 15, strokeDashoffset: 15, animation: 'draw-erase-loop 2s ease-in-out infinite 0.2s' }} />
                  <path d="M12 18v-6" style={{ strokeDasharray: 10, strokeDashoffset: 10, animation: 'draw-erase-loop 2s ease-in-out infinite 0.4s' }} />
                  <path d="M9 15l3-3 3 3" style={{ strokeDasharray: 10, strokeDashoffset: 10, animation: 'draw-erase-loop 2s ease-in-out infinite 0.6s' }} />
                </svg>
              </div>
              <h2 className="text-xl font-bold tracking-tight text-foreground">Indexing Document...</h2>
              <p className="text-sm text-muted-foreground">Extracting and vectorizing into Qdrant DB</p>
            </div>
          )}
          {isDeleting && (
            <div className="flex flex-col items-center gap-4 animate-in fade-in duration-300">
              <div className="bg-red-500/10 p-6 rounded-full flex items-center justify-center">
                <svg className="w-16 h-16 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 6L6 18" style={{ strokeDasharray: 24, strokeDashoffset: 24, animation: 'draw-erase-loop 1.2s ease-in-out infinite' }} />
                  <path d="M6 6l12 12" style={{ strokeDasharray: 24, strokeDashoffset: 24, animation: 'draw-erase-loop 1.2s ease-in-out infinite 0.2s' }} />
                </svg>
              </div>
              <h2 className="text-xl font-bold tracking-tight text-foreground">Deleting Document...</h2>
              <p className="text-sm text-muted-foreground">Removing from S3 storage and Qdrant index</p>
            </div>
          )}
        </div>,
        document.body
      )}
      {}
      {viewingDoc && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 sm:p-8">
          <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-4 border-b border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] bg-gradient-to-b from-zinc-800 to-black text-white relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              <div className="flex items-center gap-3 relative z-10">
                <FileText size={18} className="text-zinc-400" />
                <h3 className="font-bold text-sm text-zinc-100">{viewingDoc.title}</h3>
              </div>
              <div className="flex items-center gap-2 relative z-10">
                <a 
                  href={viewingDoc.url} 
                  target="_blank" 
                  rel="noreferrer"
                  className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
                  title="Open in new tab"
                >
                  <ExternalLink size={18} />
                </a>
                <button 
                  onClick={() => setViewingDoc(null)}
                  className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
            </div>
            <div className="flex-1 bg-muted/20 relative">
              <iframe 
                src={getViewerUrl(viewingDoc.url)}
                className="w-full h-full border-0 absolute inset-0"
                title="Document Viewer"
              />
            </div>
          </div>
        </div>,
        document.body
      )}
    </LockedFeature>
  );
}
