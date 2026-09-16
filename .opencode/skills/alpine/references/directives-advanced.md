# Other Directives

## x-transition

Animates `x-show` toggles. Default: fade + scale (enter 150ms, leave 75ms).
**Only works with `x-show`, not `x-if`.**

### Helper modifiers

```html
<div x-show="open" x-transition>                     <!-- defaults -->
<div x-show="open" x-transition.duration.500ms>
<div x-show="open"
     x-transition:enter.duration.500ms
     x-transition:leave.duration.1000ms>
<div x-show="open" x-transition.opacity>             <!-- fade only -->
<div x-show="open" x-transition.opacity.duration.300ms>
<div x-show="open" x-transition.scale.80>            <!-- scale only, 80% -->
<div x-show="open" x-transition.scale.origin.top>
<div x-show="open" x-transition.delay.50ms>
```

`.origin` values: `top`, `bottom`, `left`, `right` (combine two:
`.origin.top.right`).

### CSS-class syntax (full control; e.g. Tailwind)

```html
<div
    x-show="open"
    x-transition:enter="transition ease-out duration-300"
    x-transition:enter-start="opacity-0 scale-90"
    x-transition:enter-end="opacity-100 scale-100"
    x-transition:leave="transition ease-in duration-300"
    x-transition:leave-start="opacity-100 scale-100"
    x-transition:leave-end="opacity-0 scale-90"
>Hello</div>
```

Phase semantics: `enter` = whole entering phase; `enter-start` added before
insert, removed one frame after; `enter-end` added one frame after insert,
removed when the transition finishes (`leave-*` mirror this for leaving).

## x-effect

Re-runs its expression whenever any Alpine state read inside it changes. Runs
immediately on load (unlike `$watch`, which is lazy and gets an old value).

```html
<div x-data="{ label: 'Hello' }" x-effect="console.log(label)">
    <button @click="label += ' World!'">Change Message</button>
</div>
```

## x-ignore

Stops Alpine from crawling and initializing a subtree (nested Alpine markup,
third-party widgets, server-rendered islands):

```html
<div x-data="{ label: 'From Alpine' }">
    <div x-ignore>
        <span x-text="label"></span>   <!-- NOT initialized -->
    </div>
</div>
```

## x-ref + $refs

Mark and grab DOM elements — scoped replacement for `getElementById` /
`querySelector`:

```html
<button @click="$refs.text.remove()">Remove Text</button>
<span x-ref="text">Hello</span>
```

Refs must be declared statically: `:x-ref` inside `x-for` does not work in V3
(`$refs` would contain the literal string `'item.name'`). See
`magics.md` for the `$refs` magic and its limitations.

## x-cloak

Hides an element until Alpine is fully loaded, preventing the "flash" of
uninitialized markup. Requires this CSS rule on the page:

```css
[x-cloak] { display: none !important; }
```

```html
<span x-cloak x-show="false">Never 'blips' onto screen</span>
<span x-cloak x-text="message"></span>
```

Alpine removes the `x-cloak` attribute once loaded, un-hiding the element.

Template-only alternative (no global CSS needed):

```html
<template x-if="true"><span x-text="message"></span></template>
```

## x-teleport

Moves a `<template>`'s content to another part of the DOM (any
`querySelector` selector: `body`, `#modal-root`, `.portal`) while keeping the
Alpine scope. Built for modals — especially nested ones — to escape local
z-index/overflow contexts:

```html
<div x-data="{ open: false }">
    <button @click="open = ! open">Toggle Modal</button>

    <template x-teleport="body">
        <div x-show="open">
            Modal contents...
        </div>
    </template>
</div>
```

Teleported content keeps full access to the component scope (`x-data`, `$refs`,
`$root`). Native DOM events do **not** teleport: they bubble in the real DOM.
Forward them by listening on the `<template x-teleport>` element itself —
Alpine intercepts, stops propagation of the real event, and re-dispatches it
from the template:

```html
<template x-teleport="body" @click="open = false">
    <div x-show="open">Modal (click to close)</div>
</template>
```

Modals nest naturally — sibling `<template x-teleport="body">` blocks render
as siblings even when authored as children.

## x-id (+ $id)

Scopes `$id(...)` calls so repeated instances of a component get unique but
consistent IDs (labels/inputs, modals, listboxes):

```html
<div x-id="['text-input']">
    <label :for="$id('text-input')">Username</label>   <!-- for="text-input-1" -->
    <input type="text" :id="$id('text-input')">        <!-- id="text-input-1" -->
</div>

<div x-id="['text-input']">
    <label :for="$id('text-input')">Username</label>   <!-- for="text-input-2" -->
    <input type="text" :id="$id('text-input')">        <!-- id="text-input-2" -->
</div>
```

`x-id` accepts an array of ID names; all `$id('name')` calls within one scope
return the same ID ("id groups"). Groups nest; `$id('name', key)` adds a
keyed suffix inside `x-for` loops (e.g. `aria-activedescendant` listboxes).
