# Magics

Special `$`-prefixed variables available inside any Alpine expression.

## $el

The current DOM node:

```html
<button @click="$el.innerHTML = 'Hello World!'">Replace me</button>
```

## $refs

Elements marked with `x-ref` in the same component:

```html
<button @click="$refs.text.remove()">Remove Text</button>
<span x-ref="text">Hello</span>
```

Limitation: refs are static in V3 — `:x-ref="item.name"` inside `x-for` binds
nothing; `$refs` holds the literal string `'item.name'`.

## $store

Access global stores registered with `Alpine.store(...)`:

```js
document.addEventListener('alpine:init', () => {
    Alpine.store('darkMode', { on: false, toggle() { this.on = ! this.on } })
    Alpine.store('counter', 0)   // single-value store also fine
})
```

```html
<button @click="$store.darkMode.toggle()">Toggle Dark Mode</button>
<div :class="$store.darkMode.on && 'bg-black'"> ... </div>
<button @click="$store.counter++">Inc</button>
```

Store methods use `this` for store properties; stores are reactive everywhere.

## $watch

Watch a property (dot-notation for nested keys). Lazy — fires only on change;
callback receives `(newValue, oldValue)`:

```html
<div x-data="{ open: false }" x-init="$watch('open', value => console.log(value))">
<div x-data="{ foo: { bar: 'baz' } }" x-init="$watch('foo.bar', value => console.log(value))">
<div x-init="$watch('open', (value, oldValue) => console.log(value, oldValue))">
```

Deep watching: `$watch('foo', ...)` fires on nested changes but reports the
whole object as new/old value. ⚠️ Mutating the watched property inside the
callback loops forever and eventually errors.

Related: `x-effect` — immediate re-run on read-state change, no old value.

## $dispatch

Dispatch a browser event from the current element:

```html
<div @notify="alert('Hello World!')">
    <button @click="$dispatch('notify')">Notify</button>
</div>
```

- Payload → `$event.detail`: `@click="$dispatch('notify', { message: 'Hi' })"` /
  `@notify="alert($event.detail.message)"`.
- **Bubbling gotcha**: events bubble to ancestors, not siblings. Siblings must
  listen via `.window`:
  ```html
  <!-- won't work: @notify on a sibling span -->
  <!-- works: -->
  <span @notify.window="..."></span>
  <button @click="$dispatch('notify')">Notify</button>
  ```
- Cross-component: `<div x-data @set-title.window="title = $event.detail">` +
  `$dispatch('set-title', 'Hello World!')` from any other component.
- Update `x-model` programmatically: dispatch `input` —
  `$dispatch('input', 'Hello World!')` inside the `x-model` element updates the
  bound property. This is how custom input components support `x-model`
  (including non-JSON values like `File` — see x-modelable).
- Cancelable: `$dispatch('open')` returns falsy when a handler called
  `$event.preventDefault()`; gate behavior on it.
- Third arg overrides event options, e.g. `{ bubbles: false }` (then the
  listener must be on the same element).

## $nextTick

Run code after Alpine's reactive DOM updates flush:

```html
<button @click="title = 'Hello World!'; $nextTick(() => console.log($el.innerText))" x-text="title"></button>
```

Returns a promise — usable with `await`:

```html
<button @click="title = 'Changed'; await $nextTick(); console.log($el.innerText)"></button>
```

## $root

The closest `x-data` ancestor element of the current element:

```html
<div x-data data-message="Hello World!">
    <button @click="alert($root.dataset.message)">Say Hi</button>
</div>
```

## $data

The full current reactive scope as an object (merged parent + child scopes) —
pass whole scope to outside functions:

```html
<div x-data="{ greeting: 'Hello' }">
    <div x-data="{ name: 'Caleb' }">
        <button @click="sayHello($data)">Say Hello</button>
    </div>
</div>
<script>
    function sayHello({ greeting, name }) { alert(greeting + ' ' + name + '!') }
</script>
```

Rarely needed, useful for deep Alpine utilities.

## $id

Generate page-unique IDs for reusable components; see `x-id` in
`directives-advanced.md` for scoping, nesting, and keyed IDs:

```html
<input type="text" :id="$id('text-input')">   <!-- id="text-input-1" -->
<div x-id="['text-input']">                   <!-- group: same $id inside -->
    <label :for="$id('text-input')">Username</label>
    <input type="text" :id="$id('text-input')">
</div>
<li :id="$id('list-item', item.id)">          <!-- keyed suffix in loops -->
```
