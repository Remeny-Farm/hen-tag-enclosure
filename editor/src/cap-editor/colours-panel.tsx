import { ColourToggle, type ColourChoice } from './pickers.js';
import { pairedZone, type CapDesign, type CapEditorCopy, type Catalog, type ColourRole, type ZoneId } from './types.js';

type Props = {
  catalog: Catalog;
  design: CapDesign;
  copy: CapEditorCopy;
  lang: 'hu' | 'en';
  choices: ColourChoice[];
  editable: boolean;
  onColour: (zone: ZoneId, role: ColourRole) => void;
  henId: string;
};

// Step 3: one chip row per zone, explained. The rows only appear for zones
// the cap actually has (a band row without a band pattern would be noise).
export function ColoursPanel({ catalog, design, copy, lang, choices, editable, onColour, henId }: Props) {
  const zoneName = (z: ZoneId) => (catalog.zones as Record<string, { name: { hu: string; en: string } }>)[z].name[lang];
  const row = (zone: ZoneId) => {
    const other = pairedZone(catalog, zone);
    return (
      <ColourToggle
        key={zone}
        label={zoneName(zone)}
        name={`${henId}-colour-${zone}`}
        choices={choices}
        value={design.colours[zone]}
        blocked={other ? design.colours[other] : null}
        blockedReason={other ? copy.hints.numberRule : undefined}
        onChange={(role) => onColour(zone, role)}
        disabled={!editable}
      />
    );
  };
  return (
    <div className="rc-cap-panel-body">
      <p className="rc-cap-hint">{copy.hints.colours}</p>
      <div className="rc-cap-colours">
        {row('ring')}
        {row('number')}
        {row('disc')}
        {design.icon || design.centre ? row('centre') : null}
        {design.band ? row('band') : null}
      </div>
      <p className="rc-cap-hint rc-cap-hint--quiet">{copy.hints.numberRule}</p>
      <p className="rc-cap-hint rc-cap-hint--quiet">{copy.hints.window}</p>
    </div>
  );
}
