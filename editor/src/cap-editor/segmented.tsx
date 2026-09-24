import { useRef, type KeyboardEvent } from 'react';

export type SegmentItem<T extends string> = { id: T; title: string };

type Props<T extends string> = {
  label: string;
  items: SegmentItem<T>[];
  value: T;
  onChange: (id: T) => void;
  idPrefix: string;
  // Numbered when the segments are a real sequence (the design steps are:
  // the palette decides which colours the later steps can use).
  numbered?: boolean;
};

// A native-feeling segmented control that is a proper tablist: arrow keys
// move between segments, the selected one is the only tab stop, and each
// segment controls the panel `${idPrefix}-panel-${id}`.
export function Segmented<T extends string>({ label, items, value, onChange, idPrefix, numbered }: Props<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const i = Math.max(0, items.findIndex((x) => x.id === value));
    let next = i;
    if (event.key === 'ArrowRight') next = (i + 1) % items.length;
    else if (event.key === 'ArrowLeft') next = (i - 1 + items.length) % items.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = items.length - 1;
    else return;
    event.preventDefault();
    onChange(items[next].id);
    refs.current[next]?.focus();
  }

  return (
    <div className="rc-cap-seg" role="tablist" aria-label={label} onKeyDown={onKeyDown}>
      {items.map((it, i) => {
        const selected = it.id === value;
        return (
          <button
            key={it.id}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="tab"
            id={`${idPrefix}-tab-${it.id}`}
            aria-selected={selected}
            aria-controls={`${idPrefix}-panel-${it.id}`}
            tabIndex={selected ? 0 : -1}
            className="rc-cap-seg__item"
            data-selected={selected ? 'true' : undefined}
            onClick={() => onChange(it.id)}
          >
            {numbered ? <span className="rc-cap-seg__index" aria-hidden="true">{i + 1}</span> : null}
            <span className="rc-cap-seg__title">{it.title}</span>
          </button>
        );
      })}
    </div>
  );
}
