---
title: Decorators
---

## <kbd>module</kbd> `crystallize.utils.decorators`
Convenience factories and decorators for core classes. 

**Global Variables**
---------------
- **BASELINE_CONDITION**
- **CONDITION_KEY**
- **METADATA_FILENAME**
- **REPLICATE_KEY**
- **SEED_USED_KEY**

---

## <kbd>function</kbd> `resource_factory`

```python
resource_factory(
    fn: 'Callable[[FrozenContext], Any]',
    key: 'str | None' = None
) → Callable[[FrozenContext], Any]
```

Wrap a factory so the created resource is reused per thread/process. 


---

## <kbd>function</kbd> `pipeline_step`

```python
pipeline_step(cacheable: 'bool' = False) → Callable[..., PipelineStep]
```

Decorate a function and convert it into a :class:`PipelineStep` factory. 


---

## <kbd>function</kbd> `treatment`

```python
treatment(
    name: 'str',
    apply: 'Union[Callable[[FrozenContext], Any], Mapping[str, Any], None]' = None
) → Union[Callable[[Callable[[FrozenContext], Any]], Callable[..., Treatment]], Treatment]
```

Create a :class:`Treatment` from a callable or mapping. 

When called with ``name`` only, returns a decorator for functions of ``(ctx)``. Providing ``apply`` directly returns a ``Treatment`` instance. 


---

## <kbd>function</kbd> `hypothesis`

```python
hypothesis(
    verifier: 'Callable[[Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]]',
    metrics: 'str | Sequence[str] | Sequence[Sequence[str]] | None' = None,
    name: 'Optional[str]' = None
) → Callable[[Callable[[Mapping[str, Any]], float]], Hypothesis]
```

Decorate a ranker function and produce a :class:`Hypothesis`. 


---

## <kbd>function</kbd> `data_source`

```python
data_source(
    fn_or_name: 'Union[Callable[..., Any], str, None]' = None,
    register: 'bool' = False
) → Union[Callable[..., DataSource], Callable[[Callable[..., Any]], Callable[..., DataSource]]]
```

Decorate a function to produce a :class:`DataSource` factory. 

Can be used in several ways: 

1. Simple decorator (no registration): ``` @data_source```
    ... def my_source(ctx):
    ...     return [1, 2, 3]

2. Named decorator with auto-registration:
    >>> @data_source("training_data", register=True)
    ... def my_source(ctx):
    ...     return [1, 2, 3]
    >>> # Now accessible via get_datasource("training_data")

3. Register with function name:
    >>> @data_source(register=True)
    ... def training_data(ctx):
    ...     return [1, 2, 3]
    >>> # Now accessible via get_datasource("training_data")

Parameters

----------
fn_or_name:
     Either the function to decorate, or a string name for registration.
register:
     If True, register the datasource with the given name (or function name).



---

## <kbd>function</kbd> `verifier`

```python
verifier(
    fn: 'Callable[..., Any]'
) → Callable[..., Callable[[Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]]]
```

Decorate a function to produce a parameterized, picklable verifier callable. 


---

## <kbd>function</kbd> `pipeline`

```python
pipeline(*steps: 'PipelineStep') → Pipeline
```

Instantiate a :class:`Pipeline` from the given steps. 


---

## <kbd>class</kbd> `ResourceFactoryWrapper`
A picklable, callable class that wraps a resource-creating function. 

### <kbd>method</kbd> `ResourceFactoryWrapper.__init__`

```python
__init__(fn: 'Callable[[FrozenContext], Any]', key: 'str | None' = None)
```









---

## <kbd>class</kbd> `VerifierCallable`
A picklable callable that wraps the verifier function with fixed parameters. 

### <kbd>method</kbd> `VerifierCallable.__init__`

```python
__init__(
    fn: 'Callable[..., Any]',
    params: 'dict',
    param_names: 'list[str]',
    factory: 'Callable[..., Any]'
)
```









