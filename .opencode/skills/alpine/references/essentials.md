# Essentials: Installation, State, Templating, Events, Lifecycle

## Installation

Script tag (in `<head>`, **must have `defer`**):

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Hardcode the version for production. As an NPM module:

```js
import Alpine from 'alpinejs'

window.Alpine = Alpine      // optional, handy for devtools
Alpine.start()              // call exactly ONCE per page
```

Register any extension code (`Alpine.data`, `Alpine.store`, directives,
magics) **between** the import and `Alpine.start()`, or inside the
`alpine:init` event:

```js
document.addEventListener('alpine:init', () => {
    Alpine.data(...)          // and Alpine.store(...)
})
```

Note: Alpine still requires an `x-data` element for any directive to work.

## State

### Local state (`x-data`)

```html
<div x-data="{ open: false }"> ... </div>
```

- Available to all descendants; nested `x-data` inherits the parent scope, and
  a child property of the same name shadows the parent's.
- Data-less components: bare `x-data` or `x-data="{}"` (e.g. just for
  `@click="alert(...)"`).
- Single-element components can carry `x-data` on the element itself.

```html
<button x-data @click="alert('clicked!')">Click Me</button>
```

### Methods, getters, init

```html
<div x-data="{ open: false, get isOpen() { return this.open }, toggle() { this.open = ! this.open } }">
    <button @click="toggle()">Toggle</button>
    <div x-show="isOpen">Content</div>
</div>
```

Use `this.` inside the object. Method reference without parens (`@click="toggle"`)
receives the native event as its argument. A method whose only job is to return
derived state is a getter. An `init()` method on the data object is called
automatically at initialization (see Lifecycle).

### Reusable data — `Alpine.data`

```js
Alpine.data('dropdown', (initial = false) => ({
    open: initial,
    toggle() { this.open = ! this.open }
}))
```

```html
<div x-data="dropdown"> <button @click="toggle">Expand</button> <span x-show="open">…</span> </div>
<div x-data="dropdown(true)"> <!-- extra init args --> </div>
```

For backend template frameworks (Django!), the docs first recommend extracting
repeated HTML into a template partial; use `Alpine.data` for the state part.

### Global state — stores

```js
Alpine.store('tabs', { current: 'first', items: ['first', 'second', 'third'] })
```

```html
<button @click="$store.tabs.current = 'first'">First</button>
<template x-for="tab in $store.tabs.items"> ... </template>
```

Single-value stores also work: `Alpine.store('darkMode', false)` then
`$store.darkMode = ! $store.darkMode`.

## Templating

- **Text**: `x-text="title"` (any JS expression, e.g. `x-text="1 + 2"`).
- **Toggling**: `x-show` toggles `display: none` (element stays in the DOM);
  `x-if` adds/removes the element entirely and must be on a `<template>`.
- **Transitions**: `x-transition` smooths `x-show` toggles (fade+scale by
  default); customize with modifiers (`x-transition.duration.500ms`,
  `x-transition.opacity`, `x-transition:enter`/`leave`) or the full CSS-class
  syntax (see `directives-advanced.md`).
- **Binding attributes**: `x-bind` / shorthand `:` — most commonly `:class`
  (object syntax `{ 'hidden': ! open }` preserves existing classes) and
  `:style` object syntax.
- **Loops**: `x-for` on `<template>`, with `:key` for reorderable lists.
- **HTML**: `x-html` sets innerHTML — trusted content only (XSS risk).

## Events

```html
<button x-on:click="console.log('clicked')">...</button>
<button @click="console.log('clicked')">...</button>   <!-- shorthand -->
```

- Any event name: `@mouseenter`, `@keyup.enter`, `@foo` for custom events.
- `$event` gives the native event object; methods referenced without parens
  receive it as first arg.
- Key modifiers chain: `@keyup.shift.enter="..."`; key names are kebab-cased
  (`@keyup.page-down`).
- Custom events: `$dispatch('foo')` — see magics for payload/bubbling rules.
- Cross-component: `@foo.window` listens on `window`, so events dispatched
  anywhere on the page are picked up.

## Lifecycle

| Hook                          | What / when                                            |
| ----------------------------- | ------------------------------------------------------ |
| `x-init="..."`                | Runs when Alpine initializes that element (supports `await`, e.g. `posts = await (await fetch('/posts')).json()`) |
| `init()` in data object       | Called automatically before `x-init` expressions        |
| `$nextTick(() => …)`          | Runs after Alpine finishes its reactive DOM updates     |
| `$watch('key', cb)`           | Lazy: fires on data change, gets `(newValue, oldValue)` |
| `x-effect="…"`                | Immediate: runs now and on any read-state change, no old value |
| `alpine:init` event           | Before Alpine initializes the page — register data/stores here |
| `alpine:initialized` event    | After Alpine finished initializing                      |

```html
<div x-data="{ posts: [] }" x-init="posts = await (await fetch('/posts')).json()"> ... </div>
<div x-data="{ open: false }" x-init="$watch('open', value => console.log(value))"> ... </div>
```
