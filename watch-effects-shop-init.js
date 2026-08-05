/* Shop-index-only init for watch-effects.js: the balance wheel in the
   need-help-choosing panel. BalanceWheel does not honor
   prefers-reduced-motion itself (TickIn does), so gate it here. When this
   never runs, the [data-balance-wheel] div stays empty and :empty CSS hides it. */
if (!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)) {
  IglisiEffects.init({ balanceWheel: { selector: '[data-balance-wheel]' } });
}
