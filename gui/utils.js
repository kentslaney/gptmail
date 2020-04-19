let params = JSON.parse(Array.prototype.filter.call(
	document.head.getElementsByTagName("script"),
	x => x.getAttribute("type") == "params")[0].innerHTML.slice(2, -2));

function rebase(value, inbase, outbase) {
	let output = [];
	for(let remainder of value) {
		for(let digit = 0; digit < output.length; digit++) {
			remainder = inbase * output[digit] + remainder;
			output[digit] = remainder % outbase;
			remainder = Math.floor(remainder / outbase);
		}
		while(remainder) {
			output.push(remainder % outbase);
			remainder = Math.floor(remainder / outbase);
		}
	}
	return output.reverse();
}

function translate(value, inalphabet, outalphabet) {
	let rebased = rebase(value.split("").map(x => inalphabet.indexOf(x)),
		inalphabet.length, outalphabet.length);
	return rebased.map(x => outalphabet[x]).join("");
}

let uid = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz";
let digits = "/0123456789";

let common = [9, 10, 13];
for(let i = 32; i < 127; i++) if(i != 47) common.push(i);
common.push(47);
common = common.map(x => String.fromCharCode(x)).join("");

function to_uid(model, query,
		length=params.default_length, sequences=1, seed=params.default_seed) {
	return translate(translate(params.api_version + "/" + length + "/" + sequences + "/" + seed,
		digits, common.slice(0, -1)) + "/" + model + "/" + query, common, uid);
}

function from_uid(value) {
	let payload = translate(value, uid, common).split("/", 3);
	let config = translate(payload[0], common.slice(0, -1), digits)
		.split("/").map(x => parseInt(x));

	return {
		"model": payload[1], "prompt": payload[2],
		"api_version": config[0], "length": config[1],
		"sequences": config[2], "seed": config[3],
	};
}

function predict(model, query,
		length=params.default_length, sequences=1, seed=params.default_seed) {
	let loc = new URL("/" + model + "/predict", document.location);
	loc.searchParams.set("p", query);
	loc.searchParams.set("l", length);
	loc.searchParams.set("r", sequences);
	loc.searchParams.set("s", seed);
	return fetch(loc).then(res => res.json());
}

let input = {}, output = {"cancelled": {"flag": true}}, state = {
	"model": params.model, "prompt": params.default_prompt,
	"api_version": params.api_version, "length": params.default_length,
	"sequences": 1, "seed": params.default_seed,
	"output": "",
};

function update_state(clear, replace, push) {
	return () => {
		let topush = push, toreplace = replace;
		if(clear) {
			state.prompt = input.prompt.value;
			if(!output.cancelled.flag) {
				output.cancelled.flag = true;
			}

			if(state.output && state.output.length) {
				state.output = "";
				topush = true;
				toreplace = false;
			}

			populate()
		}
		let loc = state.model + "#" + to_uid(state.model, state.prompt,
			state.length, state.sequences, state.seed);
		if(toreplace) history.replaceState(state, "", loc);
		if(topush) history.pushState(state, "", loc);
	}
}

function populate() {
	document.title = "GPTMail: " + state.model;
	input.prompt.value = state.prompt;
	input.length.value = state.length;
	input.models[state.model].checked = true;

	output.prompt.textContent = state.prompt;
	output.completion.textContent = state.output;
	if(state.output && state.output.length) {
		input.run.classList.add("disabled")
	} else {
		input.run.classList.remove("disabled")
		output.completion.innerHTML += "&nbsp;";
	}
}

function resize() {
	input.prompt.style.minHeight = output.wrapper.clientHeight;

	if(input.header_right.getBoundingClientRect().left < input.mobile_left_bound) {
		document.body.classList.add("mobile")
		window.setTimeout(() => document.body.classList.add("mobile-postload"), 0)
	} else {
		document.body.classList.remove("mobile", "mobile-postload")
		input.expand_menu.checked = false
	}

	if(input.intro_autocomplete.getBoundingClientRect().left < input.intro_left_bound) {
		document.body.classList.add("narrow")
	} else {
		document.body.classList.remove("narrow")
	}
}

function run() {
	if(!state.output || !state.output.length) {
		let query = state.prompt, cancelled = {"flag": false};
		output.cancelled = cancelled;
		input.run.classList.add("loading")
		predict(state.model, query, state.length, state.sequences, state.seed)
			.then((completion) => {
				if(!cancelled.flag) {
					input.run.classList.remove("loading")
					input.run.classList.add("disabled")
					state.output = completion[0].slice(query.length);
					output.completion.textContent = state.output;
					update_state(false, true, false)()
				}
			}).catch(() => {
				if(!cancelled.flag) {
					input.run.classList.remove("loading")
					alert("Unable to connect to the server, please try again")
				}
			});
	}
}

function intro() {
	document.body.classList.add("intro")
	window.setTimeout(() => document.body.classList.add("intro-postload"), 0)
}

function intro_done() {
	document.body.classList.remove("intro", "intro-postload", "intro-stage-1", "intro-stage-2")
	window.localStorage["intro-done"] = true
}

window.addEventListener("load", () => {
	input.prompt = document.getElementById("input")
	input.prompt.addEventListener("input", update_state(true, true, false));
	input.run = document.getElementById("run")
	input.run.addEventListener("click", run)
	input.length = document.getElementById("length")
	input.length.addEventListener("input", (e) => {
		let length;
		try {
			length = parseInt(input.length.value);
		} catch(e) {
			length = 0;
		}
		if(isNaN(length) || length <= 0 || length > params.models[state.model]) {
			input.length.classList.add("invalid");
			return;
		}
		state.length = length;

		update_state(true, true, false)();
		input.length.classList.remove("invalid");
	});

	output.wrapper = document.getElementById("autocomplete-wrapper");
	output.prompt = document.getElementById("autocomplete-prompt");
	output.completion = document.getElementById("autocomplete");

	(() => {
		let encoded = window.location.hash.slice(1);
		if(encoded) {
			try {
				state = from_uid(encoded);
				return;
			} catch(e) {}
		}

		if(!state.model) {
			state.model = params.default_model;
		}
	})();

	input.models = {};
	let header_left = document.getElementById("header-left");
	input.header_right = document.getElementById("header-right");
	let header_left_after = header_left.firstElementChild;
	for(let model of Object.keys(params.models)) {
		let radio = header_left.insertBefore(document.createElement("input"), header_left_after);
		radio.setAttribute("type", "radio");
		radio.setAttribute("name", "model");
		radio.setAttribute("id", "model-" + model);
		let label = header_left.insertBefore(document.createElement("label"), header_left_after);
		label.setAttribute("for", "model-" + model);
		label.textContent = model;
		input.models[model] = radio;
	}

	populate();
	update_state(true, true, false)();

	// has to happen after populate
	for(let model of Object.keys(input.models))
		input.models[model].addEventListener("change", ((model) => () => {
			state.model = model;
			update_state(true, false, true)();
		})(model));

	if(!window.localStorage["intro-done"]) {
		intro()
	}

	let intro_left_box = document.getElementById("intro-model").getBoundingClientRect();
	input.intro_left_bound = intro_left_box.x + intro_left_box.right
	input.intro_autocomplete = document.getElementById("intro-autocomplete")

	document.getElementById("intro-skip").addEventListener("click", intro_done)
	document.getElementById("intro-next").addEventListener("click", () => {
		if(document.body.classList.contains("intro-stage-1")) {
			if(document.body.classList.contains("narrow") &&
					!document.body.classList.contains("intro-stage-2")) {
				document.body.classList.add("intro-stage-2")
			} else {
				intro_done()
			}
		} else {
			document.body.classList.add("intro-stage-1")
		}
	})

	input.expand_menu = document.getElementById("expand-menu")
	document.getElementById("help").addEventListener("click", () => {
		input.expand_menu.checked = false
		intro()
	})

	let mobile_left_box = header_left.getBoundingClientRect();
	input.mobile_left_bound = mobile_left_box.x + mobile_left_box.right
	resize()
});

window.addEventListener("popstate", (event) => {
	state = event.state;
	populate();
})

window.addEventListener("resize", resize);
