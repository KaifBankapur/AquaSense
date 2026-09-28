import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/layouts/AppShell";
import { LandingPage } from "@/pages/LandingPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AreasPage } from "@/pages/AreasPage";
import { AreaDetailPage } from "@/pages/AreaDetailPage";
import { WastagePage } from "@/pages/WastagePage";
import { PeakPage } from "@/pages/PeakPage";
import { AnomaliesPage } from "@/pages/AnomaliesPage";
import { ForecastPage } from "@/pages/ForecastPage";
import { DataPage } from "@/pages/DataPage";
import { PipelinePage } from "@/pages/PipelinePage";
import { AboutPage } from "@/pages/AboutPage";
import { AssistantPage } from "@/pages/AssistantPage";

export function App() {
  return (
    <Routes>
      {/* Marketing entry point — the dark SaaS template, outside the app shell. */}
      <Route path="/" element={<LandingPage />} />
      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/areas" element={<AreasPage />} />
        <Route path="/areas/:areaId" element={<AreaDetailPage />} />
        <Route path="/wastage" element={<WastagePage />} />
        <Route path="/peak" element={<PeakPage />} />
        <Route path="/anomalies" element={<AnomaliesPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        {/* legacy path — the template now lives at "/" */}
        <Route path="/landing" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}