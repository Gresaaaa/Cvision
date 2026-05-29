import { toAssetUrl } from "../api/client";

export function PageHero({ eyebrow, title, description, action }) {
  return (
    <section className="page-hero">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p className="hero-copy">{description}</p> : null}
      </div>
      {action ? <div className="hero-action">{action}</div> : null}
    </section>
  );
}

export function Panel({ title, subtitle, children, action }) {
  return (
    <section className="panel">
      {(title || action) && (
        <header className="panel-header">
          <div>
            {title ? <h2>{title}</h2> : null}
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function MetricStrip({ items }) {
  return (
    <div className="metric-strip">
      {items.map((item) => (
        <article className="metric-card" key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {item.note ? <small>{item.note}</small> : null}
        </article>
      ))}
    </div>
  );
}

export function StatusBadge({ value }) {
  return <span className={`status-badge status-${String(value).replaceAll("_", "-")}`}>{value}</span>;
}

export function EmptyState({ title, body }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}

export function ProfileAvatar({ imageUrl, name, size = "md", shape = "circle" }) {
  const initials = (name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("");

  return (
    <span className={`profile-avatar profile-avatar-${size} profile-avatar-${shape}`}>
      {imageUrl ? <img alt={name || "Profile"} src={toAssetUrl(imageUrl)} /> : <span>{initials || "?"}</span>}
    </span>
  );
}
