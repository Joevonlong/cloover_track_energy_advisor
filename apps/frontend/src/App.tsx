import { useState } from "react";
import LandingPage from "@/features/landing/LandingPage";
import IntakeScreen from "@/features/intake/IntakeScreen";

export default function App() {
  const [showLanding, setShowLanding] = useState(true);

  return (
    <>
      <IntakeScreen />
      {showLanding && <LandingPage onStart={() => setShowLanding(false)} />}
    </>
  );
}
