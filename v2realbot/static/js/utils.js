
API_KEY = localStorage.getItem("api-key")
var chart = null

//range switch pro chart https://jsfiddle.net/TradingView/qrb9a850/
function createSimpleSwitcher(items, activeItem, activeItemChangedCallback) {
	var switcherElement = document.createElement('div');
	switcherElement.classList.add('switcher');

	var intervalElements = items.map(function(item) {
		var itemEl = document.createElement('button');
		itemEl.innerText = item;
		itemEl.classList.add('switcher-item');
		itemEl.classList.toggle('switcher-active-item', item === activeItem);
		itemEl.addEventListener('click', function() {
			onItemClicked(item);
		});
		switcherElement.appendChild(itemEl);
		return itemEl;
	});

	function onItemClicked(item) {
		if (item === activeItem) {
			return;
		}

		intervalElements.forEach(function(element, index) {
			element.classList.toggle('switcher-active-item', items[index] === item);
		});

		activeItem = item;

		activeItemChangedCallback(item);
	}

	return switcherElement;
}

// safely handles circular references https://stackoverflow.com/questions/11616630/how-can-i-print-a-circular-structure-in-a-json-like-format
JSON.safeStringify = (obj, indent = 2) => {
    let cache = [];
    const retVal = JSON.stringify(
      obj,
      (key, value) =>
        typeof value === "object" && value !== null
          ? cache.includes(value)
            ? undefined // Duplicate reference found, discard key
            : cache.push(value) && value // Store value in our collection
          : value,
      indent
    );
    cache = null;
    return retVal;
  };

//https://www.w3schools.com/jsref/jsref_tolocalestring.asp
function format_date(datum) {
    //const options = { weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric', };
    const options = {dateStyle: "short", timeStyle: "short"}
    const date = new Date(datum);
    return date.toLocaleString('cs-CZ', options);
}


function clear_status_header() {
    $("#statusRegime").text("")
    $("#statusName").text("")
    $("#statusMode").text("")
    $("#statusAccount").text("")
    $("#statusStratvars").text("")
    //clear previous logs from rt
    $("#lines").empty()
}

// Iterate through each element in the
// first array and if some of them
// include the elements in the second
// array then return true.
function findCommonElements3(arr1, arr2) {
    return arr1.some(item => arr2.includes(item))
    }

function set_timestamp(timestamp) {
    //console.log(timestamp);
    $('#trade-timestamp').val(timestamp);
}

//KEY shortcuts
Mousetrap.bind('e', function() { 
    $( "#button_edit" ).trigger( "click" );
});
Mousetrap.bind('a', function() { 
    $( "#button_add" ).trigger( "click" );
});
Mousetrap.bind('d', function() { 
    $( "#button_dup" ).trigger( "click" );
});
Mousetrap.bind('c', function() { 
    $( "#button_copy" ).trigger( "click" );
});
Mousetrap.bind('r', function() { 
    $( "#button_run" ).trigger( "click" );
});
Mousetrap.bind('p', function() { 
    $( "#button_pause" ).trigger( "click" );
});
Mousetrap.bind('s', function() { 
    $( "#button_stop" ).trigger( "click" );
});
Mousetrap.bind('j', function() { 
    $( "#button_add_json" ).trigger( "click" );
});
Mousetrap.bind('x', function() { 
    $( "#button_delete" ).trigger( "click" );
});