"use client";

interface StatusPanelProps {
  hasNG: boolean;
  safetyViolations: string[];
  violationTypes: {
    glove: boolean;
    shoe: boolean;
    glasses: boolean;
    shirt: boolean;
  };
}

export default function StatusPanel({ hasNG, safetyViolations, violationTypes }: StatusPanelProps) {
  const shouldShowNG = hasNG || safetyViolations.length > 0;

  return (
    <aside className="h-auto lg:h-full min-h-0 flex flex-col gap-2 sm:gap-3 lg:gap-4">
      {/* OK Panel */}
      <div 
        className={`h-20 sm:h-24 md:h-28 lg:h-40 xl:h-48 2xl:h-[215px] border-3 sm:border-4 md:border-6 lg:border-8 xl:border-[10px] border-[#005496] flex items-center justify-center ${
          shouldShowNG ? 'bg-[#CFCFCF]' : 'bg-green-500'
        }`}
      >
        <span className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl 2xl:text-[95px] leading-none font-extrabold text-black">
          OK
        </span>
      </div>

      {/* NG Panel */}
      <div 
        className={`h-20 sm:h-24 md:h-28 lg:h-40 xl:h-48 2xl:h-[215px] border-3 sm:border-4 md:border-6 lg:border-8 xl:border-[10px] border-[#005496] flex items-center justify-center ${
          shouldShowNG ? 'bg-red-600' : 'bg-[#CFCFCF]'
        }`}
      >
        <span className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl 2xl:text-[95px] leading-none font-extrabold text-black">
          NG
        </span>
      </div>

      {/* PPE REQUIREMENT Panel */}
      <div className="bg-[#0B4A82] border-3 sm:border-4 md:border-[6px] border-[#005496] p-2 sm:p-3 lg:p-4 flex-1 min-h-0 flex flex-col overflow-y-auto">
        <h3
          className="text-[#E5E5E5] font-bold text-base sm:text-lg md:text-xl lg:text-2xl tracking-wide text-center flex-shrink-0"
          style={{ textShadow: "0 4px 0 rgba(0,0,0,.35)" }}
        >
          PPE REQUIREMENT
        </h3>

        {/* PPE Icons */}
        <div className="mt-2 sm:mt-3 lg:mt-4 grid grid-cols-4 gap-1.5 sm:gap-2 md:gap-3 lg:gap-4 xl:gap-6 justify-items-center flex-shrink-0">
          {[
            { src: "safety-footerwear.png", alt: "Safety Footwear", violationType: "shoe" },
            { src: "wear-goggle.png", alt: "Wear Goggle", violationType: "glasses" },
            { src: "wear-hand-protection.png", alt: "Wear Hand Protection", violationType: "glove" },
            { src: "wear-vest.png", alt: "Wear Vest", violationType: "shirt" },
          ].map(({ src, alt, violationType }) => {
            const hasViolation = violationTypes[violationType as keyof typeof violationTypes];
            return (
              <div
                key={src}
                className={`w-10 sm:w-12 md:w-14 lg:w-16 xl:w-20 rounded-[3px] sm:rounded-[4px] md:rounded-[6px] bg-[#EDEDED] shadow-[0_3px_0_rgba(0,0,0,0.25)] sm:shadow-[0_4px_0_rgba(0,0,0,0.25)] md:shadow-[0_6px_0_rgba(0,0,0,0.25)] p-1 sm:p-1.5 lg:p-2 transition-all ${
                  hasViolation 
                    ? 'border-3 sm:border-4 border-red-600 ring-2 ring-red-600 ring-offset-1 sm:ring-offset-2' 
                    : 'border border-[#BFBFBF]'
                }`}
              >
                <div className="w-full aspect-square rounded-[2px] sm:rounded-[3px] md:rounded-[4px] overflow-hidden flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={src}
                    alt={alt}
                    className="max-w-full max-h-full object-contain block"
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* WARNING BANNER */}
        <div className="mt-2 sm:mt-3 lg:mt-4 xl:mt-6 flex-shrink-0">
          <div className="relative rounded-[5px] sm:rounded-[6px] md:rounded-[8px] lg:rounded-[10px] bg-[#F39C12] px-2 sm:px-3 md:px-4 lg:px-5 py-1.5 sm:py-2 lg:py-3">
            <div className="pointer-events-none absolute inset-0 rounded-[6px] sm:rounded-[8px] md:rounded-[10px] lg:rounded-[12px] border-3 sm:border-4 md:border-[6px] border-black" />
            <div className="pointer-events-none absolute inset-[5px] sm:inset-[6px] md:inset-[8px] lg:inset-[10px] rounded-[4px] sm:rounded-[6px] md:rounded-[8px] border sm:border-2 border-black" />
            <div className="relative">
              <div className="flex items-center justify-center gap-0.5 sm:gap-1 bg-black rounded-[4px] sm:rounded-[6px] md:rounded-[8px] px-2 sm:px-3 md:px-4 lg:px-5 py-1 sm:py-1.5 lg:py-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  src="warning.png" 
                  alt="Warning" 
                  className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 lg:w-8 lg:h-8 xl:w-10 xl:h-10 object-contain" 
                />
                <span className="text-[#FBBF24] text-base sm:text-lg md:text-xl lg:text-2xl xl:text-[30px] leading-none font-extrabold tracking-wide sm:tracking-widest">
                  WARNING
                </span>
              </div>
              <div className="py-1.5 sm:py-2 lg:py-3 text-center">
                {shouldShowNG ? (
                  <div className="space-y-0.5 sm:space-y-1">
                    {hasNG && (
                      <div className="text-[#8B1E1E] font-bold text-xs sm:text-sm md:text-base lg:text-lg xl:text-xl">
                        🚫 NG DETECTED
                      </div>
                    )}
                    {safetyViolations.map((violation, index) => (
                      <div 
                        key={index} 
                        className="text-[#8B1E1E] font-bold text-[10px] sm:text-xs md:text-sm lg:text-base xl:text-lg"
                      >
                        ⚠️ {violation}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-[#8B1E1E] font-extrabold text-sm sm:text-base md:text-lg lg:text-xl xl:text-2xl tracking-wide">
                    ---
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}