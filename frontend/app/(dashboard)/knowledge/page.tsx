"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Search, UploadCloud, MessageSquare, FileText, Database, MoreHorizontal, Sparkles, Loader2, X, ExternalLink, Trash2 } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/context/UserContext";
import { uploadKnowledgeDocument, deleteKnowledgeDocument } from "@/lib/api/knowledge";
import LockedFeature from "@/components/layout/LockedFeature";

export default function KnowledgeDashboard() {
  const { profile, isHired } = useUser();
  const [documents, setDocuments] = useState<any[]>([]);
  const [searchesRun, setSearchesRun] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [toastMessage, setToastMessage] = useState<{type: 'success'|'error', text: string} | null>(null);
  const [viewingDoc, setViewingDoc] = useState<{url: string, title: string} | null>(null);

  useEffect(() => {
    const savedDocs = JSON.parse(localStorage.getItem('knowledge_documents') || '[]');
    setDocuments(savedDocs);
    const savedSearches = parseInt(localStorage.getItem('knowledge_searches') || '0', 10);
    setSearchesRun(savedSearches);
  }, []);

  const handleDeleteDocument = async (e: React.MouseEvent, docId: string, filename: string, file_url?: string) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete "${filename}" from the Knowledge Base? This cannot be undone.`)) return;

    try {
      await deleteKnowledgeDocument(filename, file_url);
      
      const updatedDocs = documents.filter(doc => doc.id !== docId);
      setDocuments(updatedDocs);
      localStorage.setItem('knowledge_documents', JSON.stringify(updatedDocs));
      
      setToastMessage({ type: 'success', text: `Successfully deleted ${filename} from the Knowledge Base.` });
    } catch (error: any) {
      setToastMessage({ type: 'error', text: error.message || "Failed to delete document." });
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
      const result = await uploadKnowledgeDocument(file);
      
      const newDoc = {
        id: Date.now().toString(),
        title: result.filename || file.name,
        uploaded: new Date().toLocaleDateString(),
        dept: "Knowledge Base",
        file_url: result.file_url
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

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-foreground animate-pulse" />
            Organizational Intelligence Hub
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Execute query pipelines and perform semantic search across corporate indices.</p>
        </div>
        <div className="flex gap-3">
          <div className="flex items-center gap-2">
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
          <Link 
            href="/knowledge/chat" 
            className="flex items-center gap-2 bg-foreground hover:bg-foreground/90 text-background px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm"
          >
            <MessageSquare size={14} />
            Query Corporate Intelligence
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-foreground rounded-2xl shadow-sm text-background flex flex-col justify-between h-40">
          <Database size={24} className="opacity-80" />
          <div>
            <h3 className="text-4xl font-black tracking-tight">{documents.length}</h3>
            <p className="text-background/80 font-bold text-[10px] uppercase tracking-wider mt-2">Indexed Knowledge Documents</p>
          </div>
        </div>
        <div className="p-6 bg-card border border-border rounded-2xl shadow-sm flex flex-col justify-between h-40">
          <Search size={24} className="text-foreground" />
          <div>
            <h3 className="text-3xl font-bold tracking-tight">{searchesRun}</h3>
            <p className="text-muted-foreground font-bold text-[10px] uppercase tracking-wider mt-2">Semantic Searches Run</p>
          </div>
        </div>
      </div>

      {/* Document Records */}
      <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-border/50 flex justify-between items-center bg-secondary/50">
          <h3 className="font-bold text-xs uppercase tracking-wider text-foreground">Recently Indexed Assets</h3>
        </div>
        <div className="divide-y divide-border/50">
          {documents.map(doc => (
            <div 
              key={doc.id} 
              className={`p-5 flex items-center justify-between transition-colors group ${doc.file_url ? 'hover:bg-secondary/30 cursor-pointer' : ''}`}
              onClick={() => {
                if (doc.file_url) {
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
              <div className="flex items-center gap-4">
                <span className="px-2.5 py-0.5 bg-secondary border border-border/50 text-[9px] uppercase tracking-wider rounded-full font-bold text-muted-foreground">
                  {doc.dept}
                </span>
                <button 
                  className="text-red-500/70 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-500/10 transition-colors" 
                  onClick={(e) => handleDeleteDocument(e, doc.id, doc.title, doc.file_url)}
                  title="Delete Document"
                >
                  <Trash2 size={16} />
                </button>
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
      {viewingDoc && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 sm:p-8">
          <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/30">
              <div className="flex items-center gap-3">
                <FileText size={18} className="text-muted-foreground" />
                <h3 className="font-bold text-sm text-foreground">{viewingDoc.title}</h3>
              </div>
              <div className="flex items-center gap-2">
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
