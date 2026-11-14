---
title: Research advances quantum computing that harnesses speed of light
source_url: https://phys.org/news/2026-11-advances-quantum-harnesses.html
author: Kayla Albert, Purdue University, via Phys.org
date: 2026-11-12
---

Research advances quantum computing that harnesses speed of light. This story comes from Phys.org, written by Kayla Albert of Purdue University, and published November 12, 2026.

Quantum computers promise to solve certain problems far faster than today's supercomputers. But they could be even faster, and use much less energy, if their basic units of information were made from light. Those units are called qubits, and building them out of single particles of light, called photons, is the goal of a group of engineers at Purdue University.

The catch is that the chips needed to make photons work as qubits are hard to build. These chips are called quantum photonic integrated circuits. Purdue researchers say they have developed possible solutions to several of the biggest problems standing in the way of building them at large scale.

First, a quick refresher. An ordinary computer works with bits, and each bit is either a zero or a one. A qubit is the quantum version. Through a phenomenon called superposition, a qubit can represent zero and one at the same time, which vastly expands how much information can be processed.

So why use photons? Photons are the smallest possible particles of light, and they have real advantages. Qubits made from single photons would move through the gates of a circuit at the speed of light, moving data faster and cutting delays when an algorithm runs. Photons are also not easily disturbed by heat or other changes in their surroundings, so they can stay stable at room temperature. Many other kinds of qubits need to be kept extremely cold, which takes a lot of energy.

The problem is scale. Today's quantum photonic chips can handle only a small number of qubits. Practical calculations would need hundreds, if not thousands, of them, and that's not yet possible with these chips.

Vladimir Shalaev, the Bob and Anne Burnett Distinguished Professor in Electrical and Computer Engineering at Purdue, put it this way: "Single photons are the building blocks of quantum photonics. The biggest challenges in scaling up a quantum photonic integrated circuit have to do with creating good single-photon sources."

Shalaev leads this work together with Alexandra Boltasseva, the Ron and Dotty Garvin Tonjes Distinguished Professor in Electrical and Computer Engineering. Their work spans Purdue's Elmore Family School of Electrical and Computer Engineering, the Birck Nanotechnology Center, and the Purdue Quantum Science and Engineering Institute. Both are well known for foundational work on controlling light at the nanoscale. Both have repeatedly been named Clarivate Highly Cited Researchers, meaning their work ranks in the top one percent of citations. Boltasseva was also named to last year's Quantum 100 list, during the United Nations-designated International Year of Quantum Science and Technology.

The article describes three advances. Let's take them one at a time.

The first is a more reliable way to produce single photons.

To act as a qubit, a photon has to be generated one at a time. That sounds simple, but it's hard. In 2021, Shalaev and Boltasseva published a study in Science Advances showing a way to emit single photons using silicon nitride. That material has become the industry standard for building quantum photonic platforms.

The method the industry has typically used to produce photons is called spontaneous parametric down-conversion. The trouble is that it produces single photons inconsistently and with low efficiency.

The Purdue team's approach is different. It emits exactly one photon, at room temperature, from dozens of locations on a silicon nitride platform, every time a laser beam passes through. The photons come from tiny changes in the material's atomic structure, called defects, which the researchers deliberately create. These defects limit the light emission to one photon at a time.

Then, at the 2022 Conference on Lasers and Electro-Optics, the team showed they could control where these defects go, and how many there are, by embedding them in nanoscale pillars on the silicon nitride. That matters because it would let the platform be manufactured more uniformly, which is essential for a real chip.

The second advance is a switch that works with a single photon.

Here's the problem. Single photons don't readily interact with each other. That makes them hard to control on a chip. In a normal computer, transistors act as switches that flip bits between zero and one. A quantum photonic chip would need switches too, so that photons can act as qubits.

Last year, in a paper in Nature Nanotechnology, the Purdue team reported a switch that operates at the level of single photons.

It builds on a mechanism the industry already uses, for example in fiber-optic communications, where one light beam is used to modulate another. That mechanism is called optical nonlinearity. A "control" beam interacts with a "probe" beam. But normally that requires power levels far too high to work with single photons.

In the Purdue method, a single photon from the control beam strikes silicon and creates an electron. That electron triggers an avalanche of more electrons. The avalanche changes how light passes through the material, specifically its refractive index, the property that governs how light travels. By changing silicon's refractive index, the device lets the probe beam pass through only when a single photon has kicked off that avalanche. In effect, one photon switches a much more powerful beam on and off.

In the lab, the researchers demonstrated this by shooting two lasers through a spatial filter onto a commercial device called a single-photon avalanche diode. That let a single photon from one beam switch another, stronger beam on and off. It's the kind of switch a quantum photonic chip would need to process information.

The third advance is a tool for predicting something called quantum decoherence.

Even though photon-based qubits are less affected by their surroundings, a single disturbance can still knock a qubit out of superposition or entanglement. That introduces errors into a quantum computer's calculations. This disturbance is called decoherence.

Purdue electrical and computer engineering professor Alexander Kildishev and graduate student Pranshu Maan led a team, including Shalaev and Boltasseva, that showed a way to anticipate decoherence before it happens. They published their findings in Nature Communications in May of this year, in a paper titled "Anticipating decoherence in quantum systems."

Boltasseva explained: "Decoherence is seemingly random, but in fact there is a certain pattern that can be recognized. This study takes an important step in identifying such a pattern using machine learning."

Using statistical-physics analysis, the team found that decoherence unfolds over time in a pattern. They then used machine learning to confirm that these patterns contain information that can be predicted. They combined these pieces into a framework that learns the behavior of a quantum system, so that decoherence could be controlled proactively, rather than only dealt with after it happens.

They focused on one major cause of decoherence, called spectral diffusion. That's when an emitted photon drifts across the electromagnetic spectrum because of natural disorder in its surroundings. Its frequency shifts, and so does its energy. Superposition only works if all the photons in a quantum system are indistinguishable from one another. So if a single photon's energy changes, superposition can fall apart.

The researchers discovered that these spectral shifts carry a kind of memory. The way a photon's frequency has wandered in the past reveals a predictable pattern over time. So the team built an algorithm with a built-in memory mechanism and trained it on data from individual quantum emitters to predict future shifts. Using those predictions, they showed that an anticipatory control approach could reduce spectral shifts by as much as twenty-fold in the systems they studied.

Why does that matter so much? Shalaev explained it with an example. "You can't get rid of decoherence, it's the law of nature that everything fluctuates. But if you recognize the pattern of decoherence and learn how to control it, then you can minimize it."

He continued: "Let's say you need a hundred qubits to run a quantum algorithm, but typically far more than that, say 10,000 qubits, to deal with errors caused by decoherence. If I minimize those errors somehow, then the number of qubits needed to run my algorithm would also be minimized."

In other words, simply being able to predict decoherence could dramatically cut the number of qubits a useful quantum computer needs.

In principle, this approach could lay the groundwork for anticipating decoherence across many quantum systems at once, which is what a scalable quantum computer would require. Those predictions could be paired with active tuning to keep different photon emitters closely aligned, making the photons they produce more indistinguishable and better synchronized.

What's next? The team plans to use tools from statistical physics to pull out hidden properties of a quantum system's fluctuating environment from its measured behavior. They'll feed those physical insights into their machine-learning models to make them better at predicting decoherence. They also want to see whether the models can pinpoint the microscopic processes that cause spectral shifts. The long-term goal is to predict and suppress decoherence before it seriously disrupts the quantum state.

So, to sum up. Purdue engineers are working on three key pieces of a light-based quantum computer: a dependable, room-temperature source that emits exactly one photon at a time; a switch that a single photon can flip; and a machine-learning tool that predicts decoherence before it happens, cutting one major source of error by up to twenty times. None of this is a finished quantum computer. But each piece tackles a real obstacle to building photonic quantum chips at the scale needed for practical work.

That was "Research advances quantum computing that harnesses speed of light," from Phys.org and Purdue University.
