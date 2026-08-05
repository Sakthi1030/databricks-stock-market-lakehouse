import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Companies } from "./pages/Companies";
import { CompanyDetail } from "./pages/CompanyDetail";
import { Movers } from "./pages/Movers";
import { Sectors } from "./pages/Sectors";
import { Watchlist } from "./pages/Watchlist";
import { Compare } from "./pages/Compare";
import { NotFound } from "./pages/NotFound";

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:symbol" element={<CompanyDetail />} />
          <Route path="/movers" element={<Movers />} />
          <Route path="/sectors" element={<Sectors />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
