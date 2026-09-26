import { Compass } from "lucide-react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Card, EmptyState } from "./components/ui";
import { HowItWorksPage } from "./pages/HowItWorksPage";
import { NewsPage } from "./pages/NewsPage";
import { RadarPage } from "./pages/RadarPage";
import { StockPage } from "./pages/StockPage";
import { TrackRecordPage } from "./pages/TrackRecordPage";

function NotFound() {
  return (
    <Card>
      <EmptyState icon={<Compass className="h-6 w-6" />} title="This page isn't on the radar">
        <Link to="/" className="font-medium text-brand hover:underline">
          Back to today's picks
        </Link>
      </EmptyState>
    </Card>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<RadarPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/track-record" element={<TrackRecordPage />} />
          <Route path="/stock/:symbol" element={<StockPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
