# Stopwatch Benchmark Patterns

## Python

```python
import time
start = time.perf_counter()
result = my_function(input)
elapsed_ms = (time.perf_counter() - start) * 1000
print(f"my_function: {elapsed_ms:.2f}ms")
```

## TypeScript / JavaScript

```ts
const start = performance.now();
const result = myFunction(input);
console.log(`myFunction: ${(performance.now() - start).toFixed(2)}ms`);
```

## C#

```csharp
using System.Diagnostics;

var sw = Stopwatch.StartNew();
var result = MyFunction(input);
sw.Stop();
Console.WriteLine($"MyFunction: {sw.Elapsed.TotalMilliseconds:F2}ms");
```
