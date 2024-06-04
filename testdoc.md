# Plotly

* MAKE_SUBPLOT Defines layout (if more then 1x1 or secondary y axis are required)

```python
fig = vbt.make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        specs=[[{"secondary_y": True}], [{"secondary_y": False}]], 
                        vertical_spacing=0.02, subplot_titles=("Row 1 title", "Row 2 title"))
```

Then the different [sr/df generic accessor](http://5.161.179.223:8000/static/js/vbt/api/generic/accessors/index.html#vectorbtpro.generic.accessors.GenericAccessor.areaplot) are added with ADD_TRACE_KWARGS and TRACE_KWARGS. Other types of plot available in [plotting module](http://5.161.179.223:8000/static/js/vbt/api/generic/plotting/index.html)

```python
#using accessor
close.vbt.plot(fig=fig, add_trace_kwargs=dict(secondary_y=False,row=1, col=1), trace_kwargs=dict(line=dict(color="blue")))
indvolume.vbt.barplot(fig=fig, add_trace_kwargs=dict(secondary_y=False, row=2, col=1))
#using plotting module
vbt.Bar(indvolume, fig=fig, add_trace_kwargs=dict(secondary_y=False, row=2, col=1))
```

* ADD_TRACE_KWARGS - determines positioning withing subplot
```python
add_trace_kwargs=dict(secondary_y=False,row=1, col=1)
```
* TRACE_KWARGS - other styling of trace
```python
trace_kwargs=dict(name="LONGS",
                  line=dict(color="#ffe476"),
                  marker=dict(color="limegreen"),
                  fill=None,
                  connectgaps=True)
```

## Example

```python
    fig = vbt.make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]], 
                            vertical_spacing=0.02, subplot_titles=("Price and Indicators", "Volume"))

    # Plotting the close price
    close.vbt.plot(fig=fig, add_trace_kwargs=dict(secondary_y=False,row=1, col=1), trace_kwargs=dict(line=dict(color="blue")))
```

# Data
## Resampling
```python
t1data = basic_data[['open', 'high', 'low', 'close', 'volume','vwap','buyvolume','sellvolume']].resample("1T")
t1data = t1data.transform(lambda df: df.between_time('09:30', '16:00').dropna()) #main session data only, no nans

t5data = basic_data[['open', 'high', 'low', 'close', 'volume','vwap','buyvolume','sellvolume']].resample("5T")
t5data = t5data.transform(lambda df: df.between_time('09:30', '16:00').dropna())

dailydata = basic_data[['open', 'high', 'low', 'close', 'volume', 'vwap']].resample("D").dropna()

#realign 5min close to 1min so it can be compared with 1min
t5data_close_realigned = t5data.close.vbt.realign_closing("1T").between_time('09:30', '16:00').dropna() 
#same with open
t5data.open.vbt.realign_opening("1h")
```
### Define resample function for custom column
Example of custom feature config [Binance Data](http://5.161.179.223:8000/static/js/vbt/api/data/custom/binance/index.html#vectorbtpro.data.custom.binance.BinanceData.feature_config).
Other [reduced functions available](http://5.161.179.223:8000/static/js/vbt/api/generic/nb/apply_reduce/index.html). (mean, min, max, median, nth ...)
```python
from vectorbtpro.utils.config import merge_dicts, Config, HybridConfig
from vectorbtpro import _typing as tp
from vectorbtpro.generic import nb as generic_nb

_feature_config: tp.ClassVar[Config] = HybridConfig(
    {
        "buyvolume": dict(
            resample_func=lambda self, obj, resampler: obj.vbt.resample_apply(
                resampler,
                generic_nb.sum_reduce_nb,
            )
        ),
        "sellvolume": dict(
            resample_func=lambda self, obj, resampler: obj.vbt.resample_apply(
                resampler,
                generic_nb.sum_reduce_nb,
            )
        )
    }
)

basic_data._feature_config = _feature_config
```

### Validate resample
```python
t2dataclose = t2data.close.rename("15MIN - realigned").vbt.realign_closing("1T")
fig = t1data.close.rename("1MIN").vbt.plot()
t2data.close.rename("15MIN").vbt.plot(fig=fig)
t2dataclose.vbt.plot(fig=fig)
```
## Persisting
```python
basic_data.to_parquet(partition_by="day", compression="gzip")  
day_data = vbt.ParquetData.pull("BAC", filters=[("group", "==", "2024-05-03")]) 
vbt.print_dir_tree("BTC-USD")#overeni directory structure
```
# Discover
```python
vbt.phelp(vbt.talib(“atr”).run) #parameters it accepts
vbt.pdir(pf) - get available properties and methods
vbt.pprint(basic_data) #to get correct shape, info about instance
```
