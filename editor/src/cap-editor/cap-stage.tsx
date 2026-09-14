import { useEffect, useRef, useState } from 'react';

import { CapPreview } from './cap-preview.js';
import type { CapDesign, CapStatus, Catalog, Layout } from './types.js';

type Props = {
  design: Pick<CapDesign, 'serial' | 'scheme' | 'icon' | 'centre' | 'band' | 'colours'>;
  catalog: Catalog;
  layout: Layout;
  title: string;
  status: CapStatus;
  statusText: string;
  // Increment to play the lock celebration (shine sweep + sparkles).
  celebrateKey: number;
  proofUrl: string | null;
  proofAlt: string;
};

const SPARKS = 10;

// The hero. The cap sits on a lit stage and "settles" with a small spring
// every time the design changes, so each tap gets a physical answer; a lock
// sweeps a shine across it and throws gold sparks. All motion is CSS on
// transform/opacity and switched off under prefers-reduced-motion.
export function CapStage({ design, catalog, layout, title, status, statusText, celebrateKey, proofUrl, proofAlt }: Props) {
  const signature = JSON.stringify([design.scheme, design.icon, design.centre, design.band, design.colours]);
  const lastSignature = useRef(signature);
  const [bump, setBump] = useState(0);

  useEffect(() => {
    if (lastSignature.current !== signature) {
      lastSignature.current = signature;
      setBump((b) => b + 1);
    }
  }, [signature]);

  return (
    <div className="rc-cap-stage" data-status={status}>
      <div className="rc-cap-stage__ring" aria-hidden="true" />
      <div className="rc-cap-stage__cap" key={bump} data-bump={bump > 0 ? 'true' : undefined}>
        <CapPreview design={design} catalog={catalog} layout={layout} title={title} />
        {celebrateKey > 0 ? (
          <div className="rc-cap-stage__fx" key={celebrateKey} aria-hidden="true">
            <span className="rc-cap-stage__shine" />
            {Array.from({ length: SPARKS }, (_, i) => (
              <svg
                key={i}
                className="rc-cap-stage__spark"
                viewBox="-6 -6 12 12"
                style={{ ['--rc-spark-angle' as string]: `${(360 / SPARKS) * i + 8}deg`, ['--rc-spark-delay' as string]: `${(i % 3) * 60}ms` }}
              >
                <path d="M0 -6 L1.5 -1.5 L6 0 L1.5 1.5 L0 6 L-1.5 1.5 L-6 0 L-1.5 -1.5 Z" />
              </svg>
            ))}
          </div>
        ) : null}
      </div>
      <p className="rc-cap-stage__status" data-status={status}>
        <span className="rc-cap-stage__dot" aria-hidden="true" />
        {statusText}
      </p>
      {proofUrl ? <img className="rc-cap-proof" src={proofUrl} alt={proofAlt} /> : null}
    </div>
  );
}
