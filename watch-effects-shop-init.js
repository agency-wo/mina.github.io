// [UI-014] watch-effects-shop-init.js — shop-index wiring for IglisiEffects
// DOES:   starts ONLY the balance wheel, and only when the visitor has not asked
//         for reduced motion (the original note below explains why the gate lives
//         here and what happens when it never runs).
// CALLS:  IglisiEffects.init
/* Shop-index-only init for watch-effects.js: the balance wheel in the
   need-help-choosing panel. BalanceWheel does not honor
   prefers-reduced-motion itself (TickIn does), so gate it here. When this
   never runs, the [data-balance-wheel] div stays empty and :empty CSS hides it. */
if (!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)) {
  IglisiEffects.init({ balanceWheel: { selector: '[data-balance-wheel]' } });
}
