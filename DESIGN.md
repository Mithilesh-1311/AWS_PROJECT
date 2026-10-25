# EOG Intent visual system

Mode: Operate. Preserve existing routes and controls; add Predictions, Live Replay and Reports.

Pinned palette: background #070B0E, panel #0C1117, selected #111920, border #23313B, text #E4ECF2, muted #9AAAB7, green #37C991, cyan #36BCE3, amber #E5AD38, red #F16D70. Square corners, one-pixel borders, no decorative shadows. Grid texture belongs to analytical charts. Body uses Inter with system fallback; measurements use JetBrains Mono with monospace fallback. Body 12–14 px, values 26–34 px, tabular numerals.

Desktop: 200 px sidebar, 52 px topbar, 16 px content padding, compact evidence strip and 60/40 analysis row. Mobile: native modal navigation drawer, stacked analytical rows, intentional table scroll and 44 px controls. Preserve focus, Escape and screen-reader names. Missing results show unavailable.

Charts use verified units, source/mode labels, linear signal segments, accessible underlying data and bounded zoom. Frequent task data never animates; occasional drawer/press feedback only, CSS 150–180 ms with cubic-bezier(0.23,1,0.32,1). Reduced motion disables movement. No minimum startup delay or decorative pipeline activity.

Verify at 1440×900 and 390×844. Replace ambiguous historical causality with explicit mode labels and fake readiness with backend readiness.
