"use client";

interface StatusPanelProps {
  mode: "slitting" | "warehouse";
  hasNG: boolean;
  safetyViolations: string[];
  violationTypes: {
    glove: boolean;
    shoe: boolean;
    glasses: boolean;
    shirt: boolean;
  };
}

export default function StatusPanel({ mode, hasNG, safetyViolations, violationTypes }: StatusPanelProps) {
  const shouldShowNG = hasNG || safetyViolations.length > 0;
  const ppeConfig = {
    slitting: [
      { src: "/tcs_slitting/safety-footerwear.png", alt: "Safety Footwear", violationType: "shoes" },
      { src: "/tcs_slitting/wear-goggle.png", alt: "Wear Goggle", violationType: "glasses" },
      { src: "/tcs_slitting/wear-hand-protection.png", alt: "Wear Hand Protection", violationType: "glove" },
      { src: "/tcs_slitting/wear-vest.png", alt: "Wear Vest", violationType: "shirt" },
    ],
    warehouse: [
      { src: "/tcs_warehouse/helmet.png", alt: "Helmet", violationType: "helmet" },
      { src: "/tcs_warehouse/shoes.png", alt: "Safety Shoes", violationType: "shoes" },
      { src: "/tcs_warehouse/vest.png", alt: "Safety Vest", violationType: "vest" },
    ],
  };

  const currentPPE = ppeConfig[mode];

  return (
    <aside className="h-auto lg:h-full lg:w-64 xl:w-72 min-h-0 flex flex-col gap-1 sm:gap-2 lg:gap-3">
      {/* OK Panel */}
      <div 
        className={`h-20 sm:h-24 lg:h-28 xl:h-32 border-1 sm:border-2 lg:border-3 flex items-center justify-center ${
          shouldShowNG 
            ? 'bg-gray-200 border-gray-300' 
            : 'bg-green-500 border-green-600'
        }`}
      >
        <span className={`text-3xl sm:text-4xl lg:text-5xl xl:text-6xl leading-none font-extrabold ${
          shouldShowNG ? 'text-black' : 'text-black'
        }`}>
          OK
        </span>
      </div>

      {/* NG Panel */}
      <div 
        className={`h-20 sm:h-24 lg:h-28 xl:h-32 border-1 sm:border-2 lg:border-3 flex items-center justify-center ${
          shouldShowNG 
            ? 'bg-red-500 border-red-600' 
            : 'bg-gray-200 border-gray-300'
        }`}
      >
        <span className={`text-3xl sm:text-4xl lg:text-5xl xl:text-6xl leading-none font-extrabold ${
          shouldShowNG ? 'text-black' : 'text-black'
        }`}>
          NG
        </span>
      </div>

      {/* PPE REQUIREMENT Panel */}
      <div className="bg-[#0B4A82] border-2 sm:border-3 border-[#005496] p-2 lg:p-3 flex-1 min-h-0 flex flex-col overflow-y-auto">
        <h3
          className="text-[#E5E5E5] font-bold text-sm sm:text-base lg:text-lg tracking-wide text-center flex-shrink-0"
          style={{ textShadow: "0 4px 0 rgba(0,0,0,.35)" }}
        >
          PPE REQUIREMENT
        </h3>

        {/* PPE Icons */}
        <div className={`mt-3 grid gap-2 lg:gap-3 justify-items-center ${
          mode === "slitting" 
            ? "grid-cols-2 sm:grid-cols-4" 
            : "grid-cols-3"
        }`}>
        {currentPPE.map(({ src, alt, violationType }) => {
          const hasViolation = violationTypes[violationType as keyof typeof violationTypes];

          // Style for Warehouse
          if (mode === "warehouse") {
            return (
              <div
                key={src}
                className={`w-14 sm:w-16 lg:w-20 xl:w-24 transition-transform duration-200 ease-out hover:-translate-y-0.5
                  ${hasViolation ? "ring-4 ring-red-500 rounded-full" : ""}`}
              >
                <div className="w-full aspect-square flex items-center justify-center p-1">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={src} alt={alt} className="w-full h-full object-contain block" />
                </div>
              </div>
            )
          }

          // Style for Slitting
          return (
            <div
              key={src}
              className={`w-10 sm:w-12 lg:w-14 xl:w-16 rounded border transition-[transform,box-shadow] duration-200 ease-out hover:-translate-y-0.5 hover:shadow-md
                ${hasViolation ? 'border-red-300 ring-2 ring-red-200 bg-red-50' : 'border-gray-200 bg-white shadow-sm'}`}
            >
              <div className="w-full aspect-square rounded-lg overflow-hidden flex items-center justify-center p-1.5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={src} alt={alt} className="max-w-full max-h-full object-contain block" />
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
                  src="/warning.png" 
                  alt="Warning" 
                  className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 lg:w-8 lg:h-8 xl:w-10 xl:h-10 object-contain" 
                />
                <span className="text-yellow-400 text-base sm:text-lg md:text-xl lg:text-2xl xl:text-[30px] leading-none font-extrabold tracking-wide sm:tracking-widest">
                  WARNING
                </span>
              </div>
              <div className="py-1.5 sm:py-2 lg:py-3 text-center">
                {shouldShowNG ? (
                  <div className="space-y-0.5 sm:space-y-1">
                    {hasNG && (
                      <div className="text-red-700 font-bold text-xs sm:text-sm md:text-base lg:text-lg xl:text-xl">
                        🚫 NG DETECTED
                      </div>
                    )}
                    {safetyViolations.map((violation, index) => (
                      <div 
                        key={index} 
                        className="text-red-700 font-bold text-[10px] sm:text-xs md:text-sm lg:text-base xl:text-lg"
                      >
                        ⚠️ {violation}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-red-700 font-extrabold text-sm sm:text-base md:text-lg lg:text-xl xl:text-2xl tracking-wide">
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