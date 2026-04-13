export const DASHBOARD_NAV = [
  { href: "/", label: "Dashboard", icon: "dashboard" },
  { href: "/channel-attribution", label: "Channel Attribution", icon: "analytics" },
  { href: "/optimization", label: "Optimization", icon: "insights" },
  { href: "/scenarios", label: "Scenarios", icon: "query_stats" },
] as const;

export type DashboardNavItem = (typeof DASHBOARD_NAV)[number];
