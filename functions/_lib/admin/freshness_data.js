export const manifest = {
  builtAt: "2026-11-07T00:00:00.000Z",
  note: "Timestamp fields copied from repository data files. This is not a live operational feed.",
  files: [
    { id: "rates", label: "US savings rates", file: "data/rates.json", timeField: "checkedAt", checkedAt: "2026-11-06" },
    { id: "yields", label: "World deposit rates", file: "data/yields.json", timeField: "checkedAt", checkedAt: "2026-11-06" },
    { id: "cards", label: "Card terms", file: "data/cards.json", timeField: "checkedAt", checkedAt: "2026-11-06" },
    { id: "markets", label: "Market series", file: "data/markets.json", timeField: "checkedAt", checkedAt: "2026-11-06" },
    { id: "fx", label: "Foreign exchange rates", file: "data/fx.json", timeField: "fetched", checkedAt: "2026-11-06" },
    { id: "crypto", label: "Crypto market snapshot", file: "data/crypto.json", timeField: "fetchedAt", checkedAt: "2026-11-06T15:42:03Z" },
    { id: "economy", label: "IMF GDP snapshot", file: "data/economy.json", timeField: "fetchedAt", checkedAt: "2026-10-25" },
    { id: "predictions", label: "Public prediction record", file: "data/predictions.json", timeField: "updated", checkedAt: "2026-11-04" },
    { id: "proptax", label: "Property-tax card fees", file: "data/proptax_fees.json", timeField: "checkedAt", checkedAt: "2026-11-05" },
    { id: "tbills", label: "Treasury bill rates", file: "data/tbills.json", timeField: "checkedAt", checkedAt: "2026-11-06" },
    { id: "events", label: "Market calendar", file: "data/events.json", timeField: "checkedAt", checkedAt: "2026-11-06" },
  ],
};
