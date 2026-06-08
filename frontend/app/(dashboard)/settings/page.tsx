export default function SettingsPage() {
  return (
    <div className="space-y-6 pb-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage enterprise workspace security, models, and integration controls.</p>
      </div>
      <div className="p-6 bg-card rounded-md shadow-sm border border-border">
        <p className="text-sm text-muted-foreground">Internal settings configurations and workspace credentials are managed automatically.</p>
      </div>
    </div>
  );
}
