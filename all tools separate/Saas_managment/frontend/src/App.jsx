import { AppShell } from "./components/layout/AppShell.jsx";
import { OverviewView } from "./views/OverviewView.jsx";
import { GhostView } from "./views/GhostView.jsx";
import { ReclamationView } from "./views/ReclamationView.jsx";
import { TrueUpView } from "./views/TrueUpView.jsx";
import { UtilizationView } from "./views/UtilizationView.jsx";
import { RenewalView } from "./views/RenewalView.jsx";
import { ForecastView } from "./views/ForecastView.jsx";
import { RecommendationsView } from "./views/RecommendationsView.jsx";
import PipelineView from "./views/PipelineView.jsx";
import { useAppStore } from "./store/useAppStore.js";

const VIEWS = {
  overview: OverviewView,
  ghost: GhostView,
  reclamation: ReclamationView,
  trueup: TrueUpView,
  utilization: UtilizationView,
  renewal: RenewalView,
  forecast: ForecastView,
  recommendations: RecommendationsView,
};

export default function App() {
  const activeView = useAppStore(s => s.activeView);
  const enterDashboard = useAppStore(s => s.enterDashboard);

  const ViewComponent = VIEWS[activeView] ?? OverviewView;

  if (!enterDashboard) {
    return <PipelineView />;
  }

  return (
    <AppShell>
      <ViewComponent />
    </AppShell>
  );
}
