import type { ReactNode } from "react";
import ControlPlaneShell from "@/components/control-plane/ControlPlaneShell";
import "./control-plane.css";

export default function ControlPlaneLayout({ children }: { children: ReactNode }) {
  return <ControlPlaneShell>{children}</ControlPlaneShell>;
}
