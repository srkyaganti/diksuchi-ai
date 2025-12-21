"use client";

import React from "react";
import { WobbleCard } from "@/components/ui/wobble-card";
import * as Icons from "lucide-react";

export function FeaturesWobble() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 max-w-7xl mx-auto w-full px-4">
      {/* Voice Feature - Wide Card */}
      <WobbleCard
        containerClassName="col-span-1 lg:col-span-2 h-full bg-gradient-to-br from-slate-700 to-slate-900 min-h-[300px] lg:min-h-[350px]"
        className=""
      >
        <div className="max-w-xs">
          <h2 className="text-left text-balance text-base md:text-xl lg:text-3xl font-semibold tracking-[-0.015em] text-white">
            Speak Your Mission, Get Instant Intelligence
          </h2>
          <p className="mt-4 text-left text-base/6 text-gray-100">
            Ask questions in Hindi, Tamil, Bengali, or any of 18+ Indian languages. Diksuchi understands you—and responds in your language.
          </p>
          <div className="mt-6 flex gap-2">
            <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs text-white font-medium">18+ Languages</span>
            <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs text-white font-medium">Hands-free</span>
          </div>
        </div>
        <Icons.Mic className="absolute -right-8 -bottom-8 h-32 w-32 text-white opacity-20" />
      </WobbleCard>

      {/* Security Feature */}
      <WobbleCard containerClassName="col-span-1 min-h-[300px] bg-gradient-to-br from-blue-900 to-slate-950">
        <h2 className="max-w-80 text-left text-balance text-base md:text-xl lg:text-3xl font-semibold tracking-[-0.015em] text-white">
          Your Intelligence Stays Your Intelligence
        </h2>
        <p className="mt-4 max-w-[26rem] text-left text-base/6 text-gray-100">
          On-premises deployment. No cloud uploads. Complete data sovereignty.
        </p>
        <div className="mt-6">
          <Icons.Shield className="h-12 w-12 text-white opacity-40" />
        </div>
      </WobbleCard>

      {/* Document Intelligence - Wide Card */}
      <WobbleCard containerClassName="col-span-1 lg:col-span-2 bg-gradient-to-br from-emerald-900 to-teal-950 min-h-[300px] lg:min-h-[350px]">
        <div className="max-w-sm">
          <h2 className="max-w-sm md:max-w-lg text-left text-balance text-base md:text-xl lg:text-3xl font-semibold tracking-[-0.015em] text-white">
            Every Technical Manual. Instantly Searchable.
          </h2>
          <p className="mt-4 max-w-[26rem] text-left text-base/6 text-gray-100">
            Hybrid Retrieval: Vector + Keyword + Knowledge Graph. Get exact information with source references.
          </p>
          <div className="mt-6 flex gap-2">
            <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs text-white font-medium">S1000D Ready</span>
            <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs text-white font-medium">Hybrid Search</span>
          </div>
        </div>
        <Icons.BookOpen className="absolute -right-10 -bottom-8 h-40 w-40 text-white opacity-15" />
      </WobbleCard>

      {/* Speed Feature */}
      <WobbleCard containerClassName="col-span-1 lg:col-span-1 bg-gradient-to-br from-indigo-900 to-purple-950 min-h-[300px]">
        <h2 className="max-w-sm text-left text-balance text-base md:text-xl lg:text-3xl font-semibold tracking-[-0.015em] text-white">
          From Hours to Seconds
        </h2>
        <p className="mt-4 max-w-[26rem] text-left text-base/6 text-gray-100">
          Reduce documentation search time by 95%. Get answers in seconds, not hours.
        </p>
        <div className="mt-6">
          <div className="text-4xl font-bold text-slate-200">95%</div>
          <p className="text-xs text-gray-400 mt-2">Faster Search</p>
        </div>
      </WobbleCard>
    </div>
  );
}
