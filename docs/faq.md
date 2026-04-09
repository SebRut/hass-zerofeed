# FAQ

How do I make the ramp-up more gradual?
- Lower Sigmoid steepness so the preference for higher SoC grows more gently.

I want fuller batteries to do more of the work.
- Increase Sigmoid steepness, or set a High SoC priority threshold (for example 90%).

What does "balance point" mean?
- It is the SoC where batteries are treated as neutral. A positive offset favors higher SoC; a negative offset makes the algorithm more willing to use lower SoC batteries.

I want the sharing to be more even.
- Lower Sigmoid steepness and consider a negative Sigmoid center offset.

I want only very full batteries to discharge first.
- Set High SoC priority threshold (for example 90%). Others will only be used if the target cannot be met.

Why does a battery not discharge at all?
- Check its min SoC threshold and the current SoC. At or below the threshold, it is skipped.

How do I cap one battery lower than the others?
- Enable the "Max power override" entity for that battery in the Entity Registry, then set a value in W. Set it to 0 to disable the override.

How do I temporarily disable a battery?
- Turn off the "Battery enabled" switch on that battery's device page.
