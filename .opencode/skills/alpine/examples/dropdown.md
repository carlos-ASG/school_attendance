# Example: Dropdown and Modal

The two canonical Alpine patterns. Covers `x-data`, `x-show`, `x-if`,
`@click.outside`, `x-transition` (both syntaxes), `x-cloak`, `$refs`, and
`x-teleport`.

## Dropdown

```html
<div x-data="{ open: false }">
    <button @click="open = ! open" :aria-expanded="open">Toggle</button>

    <div
        x-cloak
        x-show="open"
        x-transition:enter="transition ease-out duration-200"
        x-transition:enter-start="opacity-0 scale-95"
        x-transition:enter-end="opacity-100 scale-100"
        x-transition:leave="transition ease-in duration-150"
        x-transition:leave-start="opacity-100 scale-100"
        x-transition:leave-end="opacity-0 scale-95"
        @click.outside="open = false"
        @keydown.escape.window="open = false"
    >
        Menu contents...
    </div>
</div>
```

Key points:

- `x-cloak` prevents the menu from flashing on page load (needs the
  `[x-cloak] { display: none !important; }` CSS rule — already present in this
  repo's design system).
- `@click.outside` only fires while the element is visible, so toggling via
  the button doesn't immediately re-close it.
- `@keydown.escape.window` closes from anywhere on the page.

Minimal CSS-class-free version: `x-show="open" x-transition.opacity` (fade
only) is often enough.

## Modal (teleported)

```html
<div x-data="{ open: false }">
    <button @click="open = true">Open Modal</button>

    <template x-teleport="body">
        <div
            x-show="open"
            x-transition.opacity
            class="fixed inset-0 z-50 flex items-center justify-center"
            @click.self="open = false"
            @keydown.escape.window="open = false"
        >
            <div
                x-show="open"
                x-transition:enter="transition ease-out duration-200"
                x-transition:enter-start="opacity-0 scale-90"
                x-transition:enter-end="opacity-100 scale-100"
                x-transition:leave="transition ease-in duration-150"
                x-transition:leave-start="opacity-100 scale-100"
                x-transition:leave-end="opacity-0 scale-90"
            >
                Modal contents...
            </div>
        </div>
    </template>
</div>
```

Key points:

- `x-teleport="body"` escapes any `overflow`/`z-index` limits of ancestors —
  required when the trigger sits inside a stacking context.
- `x-if` could be used instead of `x-show` when the modal shouldn't exist in
  the DOM at all (e.g. forms re-fetched per open), but then drop the
  transitions (`x-transition` needs `x-show`).
- `@click.self` closes on backdrop clicks but not on clicks inside the panel.
- Nested modals: give each its own `<template x-teleport="body">`; they render
  as siblings.
- Conditional DOM access right after opening:
  `open = true; $nextTick(() => $refs.input.focus())` with `x-ref="input"` on
  the panel's first field (must be inside `x-show` scope, not behind `x-if`
  timing issues).
