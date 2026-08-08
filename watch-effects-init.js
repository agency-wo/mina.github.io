// [UI-013] watch-effects-init.js — homepage wiring for IglisiEffects
// DOES:   enables all four effects with the homepage's selectors; nothing else.
// CALLS:  IglisiEffects.init (watch-effects.js must be loaded first)
IglisiEffects.init({
  loupe:        { section: '#watches', cards: '.watch-card' },
  tickIn:       true,
  trail:        { section: '.hero-bg' },
  balanceWheel: { selector: '[data-balance-wheel]' }
});
