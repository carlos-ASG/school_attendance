# Example: Global Store + Reusable Component

Cross-component state with `Alpine.store`, reusable logic with `Alpine.data`,
and unique IDs with `x-id`/`$id` — the patterns used for repeated, server-
rendered components (Django cotton components).

## Global store

```html
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.store('tabs', {
            current: 'first',
            items: ['first', 'second', 'third'],
        })

        Alpine.store('darkMode', {
            on: false,
            toggle() { this.on = ! this.on },
        })
    })
</script>

<button @click="$store.darkMode.toggle()">Toggle Dark Mode</button>
<div :class="$store.darkMode.on && 'bg-black'"> ... </div>

<div x-data>
    <button @click="$store.tabs.current = 'second'">Second</button>
</div>
<div x-data>
    <template x-for="tab in $store.tabs.items">
        <span x-show="$store.tabs.current === tab" x-text="tab"></span>
    </template>
</div>
```

Every `x-data` component reads/writes `$store.tabs.current` reactively — no
props or events needed. Single-value stores work too:
`Alpine.store('counter', 0)` → `$store.counter++`.

## Reusable component (`Alpine.data` + `x-id`)

Register once inside `alpine:init` (before Alpine starts):

```html
<script>
    document.addEventListener('alpine:init', () => {
        Alpine.data('counter', (start = 0) => ({
            count: start,

            init() {
                console.log('each instance initializes me')
            },

            increment() { this.count++ },
        }))
    })
</script>
```

Use anywhere; `x-id` keeps repeated instances' IDs unique for
`<label>`/`<input>` pairing:

```html
<div x-data="counter" x-id="['count']">
    <label :for="$id('count')">Count</label>
    <input type="number" :id="$id('count')" x-model.number="count">
    <button @click="increment">+</button>
    <span x-text="count"></span>
</div>

<div x-data="counter(10)">  <!-- instance 2 starts at 10; IDs get -2 suffix -->
    ...
</div>
```

Key points:

- `init()` runs automatically per instance, before `x-init` expressions.
- Components accept constructor args: `x-data="counter(10)"`.
- `x-modelable="count"` on the root (plus `x-model` from the parent) would
  additionally expose `count` as a two-way binding API for wrapper components.
- Store/`Alpine.data` registration must happen inside `alpine:init` (or
  between `import Alpine` and `Alpine.start()` when bundling).
- In this repo, such blocks are natural candidates for django-cotton
  components — co-load the `django-cotton` skill for `<c-...>` syntax and the
  cotton/Alpine interop rules.
