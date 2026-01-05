---
title: Registry
---

## <kbd>module</kbd> `crystallize.datasources.registry`
Datasource registry for string-based lookups. 

This module provides a simple registry pattern that allows datasources to be referenced by name instead of requiring direct imports. This is particularly useful when treatments need to reference datasources defined elsewhere. 

Example 
------- ``` from crystallize import data_source, get_datasource```
`````` ``` @data_source("my_data")```
... def load_data(ctx):
...     return [1, 2, 3]
`````` ``` # Later, in another module, without importing load_data:```
``` ds = get_datasource("my_data")``` ``` data = ds.fetch(ctx)```


**Global Variables**
---------------
- **TYPE_CHECKING**

---

## <kbd>function</kbd> `register_datasource`

```python
register_datasource(name: 'str', datasource: "'DataSource'") → None
```

Register a datasource by name. 

Parameters 
---------- name:  Unique name for the datasource. datasource:  The datasource instance to register. 

Raises 
------ ValueError  If a datasource with this name is already registered. 

Example 
------- ``` register_datasource("training_data", my_datasource)```



---

## <kbd>function</kbd> `get_datasource`

```python
get_datasource(name: 'str') → 'DataSource'
```

Retrieve a registered datasource by name. 

Parameters 
---------- name:  The name of the datasource to retrieve. 

Returns 
------- DataSource  The registered datasource. 

Raises 
------ KeyError  If no datasource is registered with this name. 

Example 
------- ``` ds = get_datasource("training_data")```
``` data = ds.fetch(ctx)``` 


---

## <kbd>function</kbd> `unregister_datasource`

```python
unregister_datasource(name: 'str') → Optional['DataSource']
```

Remove a datasource from the registry. 

Parameters 
---------- name:  The name of the datasource to remove. 

Returns 
------- Optional[DataSource]  The removed datasource, or None if it wasn't registered. 


---

## <kbd>function</kbd> `list_datasources`

```python
list_datasources() → list[str]
```

List all registered datasource names. 

Returns 
------- list[str]  Names of all registered datasources. 


---

## <kbd>function</kbd> `clear_registry`

```python
clear_registry() → None
```

Clear all registered datasources. Mainly for testing. 


