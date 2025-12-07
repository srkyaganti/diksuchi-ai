export function FeatureCard({
  title,
  description,
  icon
}: {
  title: string;
  description: string;
  icon?: string;
}) {
  return (
    <div className="border rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        {icon && <span className="text-2xl leading-none">{icon}</span>}
        <div className="flex-1">
          <h4 className="font-semibold mb-2 text-foreground">{title}</h4>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
}
