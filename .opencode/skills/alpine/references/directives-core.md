# Core Directives

## x-data

Defines an Alpine component and its reactive data.

- **Scope**: properties are visible to all children, even inside nested
  `x-data`; child shadowing wins on name conflicts.
- **Methods**: plain JS methods with `this` context; `@click="toggle"` works
  without parens.
- **Getters**: `get isOpen() { return this.open }` for expressive derived state
  (not cached like Vue computed).
- **Data-less**: `x-data` (bare) or `x-data="{}"`.
- **Reusable**: extract with `Alpine.data('name', () => ({...}))` inside
  `alpine:init`, then `x-data="name"` (extra args: `x-data="name(arg1, ...)"`).

## x-init

Runs when the element initializes; supports `await`. Can be added to any
element inside or outside `x-data`.

```html
<div x-data="{ posts: [] }" x-init="posts = await (await fetch('/posts')).json()">...</div>
<div x-init="$nextTick(() => { ... })"></div>
```

Order when both exist: the data object's `init()` method first, then `x-init`.

## x-show

Toggles `display: none` — element stays in the DOM (state preserved).

```html
<div x-data="{ open: false }">
    <button @click="open = ! open">Toggle</button>
    <div x-show="open">Dropdown contents...</div>
</div>
```

- Pair with `x-transition` for animation; pairs naturally with `x-cloak` to
  avoid the flash before Alpine loads.
- `.important` modifier: `x-show.important="open"` → `display: none !important`
  (for CSS that already forces `display` with `!important`).

## x-if

Adds/removes the element entirely. **Must be on a `<template>` tag** (which
contains exactly one root element).

```html
<template x-if="open">
    <div>Contents...</div>
</template>
```

Caveats: does NOT support `x-transition`; template must have a single root.

## x-bind (shorthand `:`)

Sets HTML attributes from expressions.

```html
<input type="text" x-bind:placeholder="placeholderText">
<input type="text" :placeholder="placeholderText">
<button :disabled="busy">Save</button>
```

### Binding classes

```html
<div :class="open ? '' : 'hidden'">      <!-- short-circuit: open || 'hidden' -->
<div :class="closed && 'hidden'">
<div :class="{ 'hidden': ! show }">      <!-- object syntax -->
```

`x-bind:class` is special: Alpine preserves existing classes on the element
(`class="opacity-50" :class="hide && 'hidden'"` → `"opacity-50 hidden"`). The
object syntax is the only form that lets a static `class="hidden"` attribute
and Alpine share toggling of the same class.

### Binding styles

Object syntax, mixes with existing inline styles:

```html
<div style="padding: 1rem;" :style="{ color: 'red', display: 'flex' }">
```

### Binding multiple directives at once (`x-bind="obj"`)

Inside an `Alpine.data` component, expose attribute/directive bundles:

```js
Alpine.data('dropdown', () => ({
    open: false,
    trigger: {
        ['x-ref']: 'trigger',
        ['@click']() { this.open = true },
    },
    dialogue: {
        ['x-show']() { return this.open },
        ['@click.outside']() { this.open = false },
    },
}))
```

```html
<button x-bind="trigger">Open Dropdown</button>
<span x-bind="dialogue">Dropdown Contents</span>
```

For a bound `x-for`, return an expression **string**:
`['x-for']() { return 'item in items' }`.

## x-on (shorthand `@`)

Runs code on DOM events. Lowercase event names in HTML; use `.camel` (or
`.dot`) modifiers for camelCase / dotted custom event names.

### Event object

```html
<button @click="alert($event.target.getAttribute('message'))" message="Hello">…</button>
<button @click="handleClick">…</button>  <!-- handleClick(e) receives the event -->
```

### Keyboard / mouse modifiers

Chain them: `@keyup.shift.enter`, `@click.shift`, `@keydown.escape`,
`@keyup.page-down`. Common: `.shift` `.enter` `.space` `.ctrl` `.cmd` `.meta`
`.alt` `.up/.down/.left/.right` `.escape` `.tab` `.caps-lock` `.equal`
`.period` `.comma` `.slash`.

### All modifiers

| Modifier        | Effect                                                          |
| --------------- | --------------------------------------------------------------- |
| `.prevent`      | `event.preventDefault()` — e.g. `<form @submit.prevent>`        |
| `.stop`         | `event.stopPropagation()`                                       |
| `.outside`      | Fires only for clicks outside the element (visibility-gated)     |
| `.window`       | Listen on `window` (cross-component communication)               |
| `.document`     | Listen on `document`                                             |
| `.once`         | Handler runs a single time                                       |
| `.debounce`     | Wait for inactivity (250ms; `.debounce.500ms` custom)            |
| `.throttle`     | Call at most every 250ms (`.throttle.750ms` custom) — good for `@scroll.window` |
| `.self`         | Only if the event originated on this element, not a child        |
| `.camel`        | `@custom-event.camel` listens for `customEvent`                  |
| `.dot`          | `@custom-event.dot` listens for `custom.event`                   |
| `.passive`      | Don't block scroll (touch/wheel listeners)                       |
| `.passive.false`| Make touch/wheel cancelable again so `preventDefault` works      |
| `.capture`      | Capture phase — runs before bubbling handlers                    |

## x-text / x-html

```html
<div x-data="{ username: 'calebporzio' }">
    Username: <strong x-text="username"></strong>
</div>
```

`x-html` sets innerHTML — **trusted content only** (XSS risk with
user-provided content).

## x-model

Two-way binding: `<input type="text" x-model="message">`.

Works with: text inputs, `<textarea>`, checkbox (single → boolean; multiple
with same `x-model` → array of `value`s), radio, `<select>` (single/multiple,
incl. `x-for`-generated options and disabled placeholder), `range`.

Modifiers:

| Modifier          | Behavior                                                       |
| ----------------- | -------------------------------------------------------------- |
| `.lazy` / `.change` | Sync when focus leaves and value changed                      |
| `.blur`           | Sync on losing focus regardless of change                       |
| `.enter`          | Sync on Enter key (does NOT prevent form submit)                |
| combine           | `x-model.change.blur.enter="message"`                          |
| `.number`         | Store as number instead of string                               |
| `.boolean`        | Store as boolean (`"true"`/`"false"`/`1`/`0`)                   |
| `.debounce`       | Debounce updates (250ms; `.debounce.500ms`)                     |
| `.throttle`       | Throttle updates (250ms; `.throttle.500ms`)                     |
| `.fill`           | Use the input's `value` attribute to seed an empty bound property |

Programmatic access on the bound element: `el._x_model.get()` /
`el._x_model.set(value)` — for overriding x-model behavior or allowing
x-model on non-input elements.

## x-modelable

Exposes internal state as the target of an outer `x-model` (Vue-style
v-model wrapper, useful for reusable backend-templated components):

```html
<div x-data="{ number: 5 }">
    <div x-data="{ count: 0 }" x-modelable="count" x-model="number">
        <button @click="count++">Increment</button>
    </div>
    Number: <span x-text="number"></span>
</div>
```

Values cross the boundary via JSON clone: strings/numbers/booleans/null/arrays/
plain objects only — NOT `File`, `FileList`, `Map`, `Set`, `Date`, class
instances, DOM nodes. For those, omit `x-modelable` and dispatch `input`:

```html
<div x-model="files">
    <input type="file" multiple @change="$dispatch('input', Array.from($event.target.files))">
</div>
```

## x-for

```html
<ul x-data="{ colors: ['Red', 'Orange', 'Yellow'] }">
    <template x-for="color in colors">
        <li x-text="color"></li>
    </template>
</ul>
```

- **Must** be on `<template>`; template must contain exactly **one root**.
- Objects: `x-for="(value, index) in car"`; ranges: `x-for="i in 10"`.
- Index: `x-for="(color, index) in colors"`.
- Keys for reorderable lists: `<template x-for="color in colors" :key="color.id">`.
