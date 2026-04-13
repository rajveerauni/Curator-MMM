import type { ReactNode } from "react";

import { CompanyIntelProvider } from "@/components/company-intel-context";
import DashboardShell from "@/components/dashboard-shell";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <CompanyIntelProvider>
      <DashboardShell>{children}</DashboardShell>
    </CompanyIntelProvider>
  );
}
