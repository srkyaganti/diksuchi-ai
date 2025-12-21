"use client";

import React from "react";
import { InfiniteMovingCards } from "@/components/ui/infinite-moving-cards";

const documentExamples = [
  {
    quote: "What's the pre-flight hydraulic system check procedure?",
    name: "Flight Operations",
    title: "Pilot — Aircraft Maintenance",
  },
  {
    quote: "Show me torque specifications for main wing attachment bolts",
    name: "Engineering Review",
    title: "Senior Engineer — Structural Analysis",
  },
  {
    quote: "List all components requiring titanium alloy grade 5",
    name: "Procurement",
    title: "Contractor — Supply Chain Management",
  },
  {
    quote: "Find all S1000D documents related to avionics system failures",
    name: "Troubleshooting",
    title: "Technician — Fault Diagnosis",
  },
  {
    quote: "What are the maintenance intervals for engine overhaul?",
    name: "Predictive Maintenance",
    title: "Operations Officer — Scheduled Maintenance",
  },
  {
    quote: "Compare part compatibility across three different aircraft models",
    name: "Technical Comparison",
    title: "Systems Engineer — Cross-Platform Analysis",
  },
  {
    quote: "Get safety protocols for hazardous materials handling",
    name: "Safety & Compliance",
    title: "Safety Officer — Risk Management",
  },
  {
    quote: "Extract all performance specifications for mission planning",
    name: "Mission Planning",
    title: "Operations Coordinator — Flight Planning",
  },
  {
    quote: "Identify all deprecated components in our fleet",
    name: "Fleet Management",
    title: "Technical Director — Modernization",
  },
  {
    quote: "What documentation updates were made in the last quarter?",
    name: "Knowledge Management",
    title: "Training Officer — Curriculum Updates",
  },
];

export function DocumentIntelligenceCards() {
  return (
    <div className="h-[30rem] rounded-lg flex flex-col antialiased items-center justify-center relative overflow-hidden">
      <InfiniteMovingCards
        items={documentExamples}
        direction="right"
        speed="slow"
        pauseOnHover={true}
      />
    </div>
  );
}
