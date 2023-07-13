word = "buy_if_not_something"


if word.endswith("something") and word[:-len] == "not_":
    print("Word meets the condition.")
else:
    print("Word does not meet the condition.")