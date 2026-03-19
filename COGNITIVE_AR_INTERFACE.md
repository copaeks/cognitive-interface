<!DOCTYPE html>

<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Cognitive AR Interface</title>
<script src="https://statics.moonshot.cn/kimi-ppt/html-gen/static/tailwindcss@4_0805.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Chiron+Hei+HK:wght@400;700&amp;family=Hedvig+Letters+Sans:wght@400;700&amp;family=Quattrocento+Sans:wght@400;700&amp;family=Coda:wght@400;800&amp;display=swap" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0/css/all.min.css" rel="stylesheet"/>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.0/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style type="text/tailwindcss">
        @layer utilities {
            .ppt-slide {
                @apply relative w-[1280px] h-[720px] mx-auto p-[40px] box-border overflow-hidden mb-[40px];
            }
        }
    </style>
<style>
        body {
            color: #E5E5E5;
            font-family: 'Quattrocento Sans', sans-serif;
        }
        .font-display {
            font-family: 'Chiron Hei HK', sans-serif;
        }
        .font-brand {
            font-family: 'Hedvig Letters Sans', sans-serif;
        }
        .font-caption {
            font-family: 'Coda', sans-serif;
        }
    </style>
</head>
<body class="bg-gray-900 py-8">
<!-- Slide 1: Cover -->
<div class="ppt-slide !bg-[#0A0A0A]" type="cover">
<img alt="Cover" class="absolute inset-0 w-full h-full object-cover opacity-60" src="cover_cognitive_ar.png"/>
<div class="absolute inset-0 bg-gradient-to-br from-[#0A0A0A]/95 via-[#0A0A0A]/70 to-transparent"></div>
<div class="relative h-full flex flex-col justify-center">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">The First Spatial Operating System for Human Thought</span>
</div>
<h1 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.95]">Cognitive<br/>AR Interface</h1>
<div class="w-32 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90 mb-3">Externalize Your Mind</p>
<p class="text-2xl text-[#E5E5E5]/70 mb-12">See in 3D What Others Imagine in 2D</p>
<div class="flex items-center gap-6 text-base text-[#E5E5E5]/60">
<div class="flex items-center gap-2">
<i class="fas fa-user text-[#34D399]"></i>
<span>Ivan Vankov Fortanet @copaeks</span>
</div>
<div class="flex items-center gap-2">
<i class="fas fa-map-marker-alt text-[#34D399]"></i>
<span>Cuernavaca, Mexico</span>
</div>
<div class="flex items-center gap-2">
<i class="fas fa-shield-alt text-[#34D399]"></i>
<span>MIT License</span>
</div>
</div>
</div>
</div>
<!-- Slide 2: Table of Contents -->
<div class="ppt-slide !bg-[#0A0A0A]" type="table_of_contents">
<div class="h-full flex flex-col">
<div class="mb-8">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Navigation</span>
<h2 class="font-display text-5xl font-bold text-[#E5E5E5] mt-2">Contents</h2>
</div>
<div class="flex-1 grid grid-cols-2 gap-6">
<div class="flex items-start gap-4 p-5 bg-[#2A2A2A]/40 rounded-lg border-l-4 border-[#34D399]">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">01</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-2">The Manifesto</h3>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">Why This Exists — The cognitive mismatch between 3D thinking and 2D interfaces</p>
</div>
</div>
<div class="flex items-start gap-4 p-5 bg-[#2A2A2A]/40 rounded-lg border-l-4 border-[#34D399]">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">02</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-2">The Breakthrough</h3>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">Passive Acoustic Shadow Tracking (PAST) — Tracking silence, not presence</p>
</div>
</div>
<div class="flex items-start gap-4 p-5 bg-[#2A2A2A]/40 rounded-lg border-l-4 border-[#34D399]">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">03</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-2">System Architecture</h3>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">The Hardware Trinity &amp; Four Scalability Layers</p>
</div>
</div>
<div class="flex items-start gap-4 p-5 bg-[#2A2A2A]/40 rounded-lg border-l-4 border-[#34D399]">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">04</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-2">APP_CENTER &amp; Economic Layer</h3>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">The Independent Hub &amp; Contextual Consent Ads (CCA)</p>
</div>
</div>
<div class="flex items-start gap-4 p-5 bg-[#2A2A2A]/40 rounded-lg border-l-4 border-[#34D399]">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">05</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-2">Use Cases &amp; Applications</h3>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">From Factory to Living Room — Industrial, Consumer, Education</p>
</div>
</div>
<div class="flex items-start gap-4 p-5 bg-[#2A2A2A]/40 rounded-lg border-l-4 border-[#34D399]">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">06</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-2">Technical Specs &amp; Roadmap</h3>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">Engineering Reality — Specifications &amp; Development Timeline</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 3: Chapter 1 -->
<div class="ppt-slide !bg-[#0A0A0A]" type="chapter">
<img alt="Chapter 1" class="absolute inset-0 w-full h-full object-cover opacity-40" src="https://kimi-web-img.moonshot.cn/img/images.stockcake.com/bc52434e58af5e20e0cb5cacebd048b6ae8a3449.jpg"/>
<div class="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-[#0A0A0A]/90 to-[#0A0A0A]/60"></div>
<div class="relative h-full flex items-center">
<div class="max-w-3xl">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase mb-4 block">Chapter One</span>
<h2 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.9]">The<br/>Manifesto</h2>
<div class="w-40 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90">Why This Exists</p>
</div>
</div>
</div>
<!-- Slide 4: The Cognitive Mismatch -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-6">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">The Problem</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Cognitive Mismatch</h2>
</div>
<div class="flex-1 flex gap-6">
<div class="flex-1 flex flex-col gap-5">
<div class="bg-[#2A2A2A]/40 p-6 rounded-lg flex-1 flex flex-col justify-center">
<div class="flex items-start gap-4">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-brain text-[#34D399] text-xl">
</i>
</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">How We Think</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">
                                        The human brain evolved over millions of years to think in
                                        <strong class="text-[#34D399]">3D space</strong>
                                        —grabbing concepts, rotating ideas, placing memories in physical locations. Our cognition is inherently spatial, multimodal, and embodied.
                                    </p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-6 rounded-lg flex-1 flex flex-col justify-center">
<div class="flex items-start gap-4">
<div class="w-12 h-12 rounded-full bg-[#555555]/20 flex items-center justify-center shrink-0">
<i class="fas fa-desktop text-[#555555] text-xl">
</i>
</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">How We're Forced to Work</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">
                                        For 50 years, we've been forced to compress
                                        <strong class="text-[#34D399]">multidimensional thought</strong>
                                        into 2D rectangles—screens, paper, touch interfaces. This creates a cognitive bottleneck that limits creativity and understanding.
                                    </p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-6 rounded-lg flex-1 flex flex-col justify-center">
<div class="flex items-start gap-4">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-compress-arrows-alt text-[#34D399] text-xl">
</i>
</div>
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">The Compression Loss</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">
                                        Every time we flatten a 3D concept into 2D, we lose
                                        <strong class="text-[#34D399]">spatial relationships, depth cues, and embodied understanding</strong>
                                        . We're using stone-age brains with space-age limitations.
                                    </p>
</div>
</div>
</div>
</div>
<div class="w-96 flex flex-col gap-5">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-lg font-bold text-[#E5E5E5] mb-4">The Evolutionary Gap</h3>
<div class="space-y-4">
<div>
<div class="flex justify-between items-center mb-2">
<span class="text-base text-[#E5E5E5]/80">Brain Evolution</span>
<span class="text-base text-[#34D399] font-bold">2M years</span>
</div>
<div class="w-full bg-[#555555]/20 rounded-full h-2">
<div class="bg-[#34D399] h-2 rounded-full" style="width: 100%">
</div>
</div>
</div>
<div>
<div class="flex justify-between items-center mb-2">
<span class="text-base text-[#E5E5E5]/80">2D Interfaces</span>
<span class="text-base text-[#555555] font-bold">50 years</span>
</div>
<div class="w-full bg-[#555555]/20 rounded-full h-2">
<div class="bg-[#555555] h-2 rounded-full" style="width: 2%">
</div>
</div>
</div>
</div>
<p class="text-sm text-[#E5E5E5]/60 mt-4 italic">Our tools have evolved faster than our ability to use them naturally.</p>
</div>
<div class="bg-[#34D399]/10 p-5 rounded-lg border border-[#34D399]/30 flex-1 flex flex-col justify-center">
<div class="text-center">
<i class="fas fa-quote-left text-[#34D399] text-2xl mb-3">
</i>
<p class="font-brand text-xl text-[#E5E5E5] leading-relaxed mb-3">"The human brain didn't evolve to read text on glowing rectangles. It evolved to navigate 3D space, manipulate objects, and think spatially."</p>
<p class="text-base text-[#E5E5E5]/60">— Cognitive Science Research</p>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg">
<h4 class="font-display text-base font-bold text-[#E5E5E5] mb-3">Current AR/VR Attempts</h4>
<div class="space-y-2 text-base text-[#E5E5E5]/70">
<div class="flex items-center gap-2">
<i class="fas fa-times text-red-500">
</i>
<span>Add more screens (bulky headsets)</span>
</div>
<div class="flex items-center gap-2">
<i class="fas fa-times text-red-500">
</i>
<span>Cameras everywhere (privacy invasion)</span>
</div>
<div class="flex items-center gap-2">
<i class="fas fa-times text-red-500">
</i>
<span>Battery-draining processors</span>
</div>
<div class="flex items-center gap-2">
<i class="fas fa-times text-red-500">
</i>
<span>Cloud dependency (latency)</span>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 5: The Exception Philosophy -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Core Philosophy</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Exception Philosophy</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-2">Exception Kills Structure — A Paradigm Inversion</p>
</div>
<div class="flex-1 flex gap-4">
<div class="flex-[55] flex flex-col gap-3">
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg">
<h3 class="font-display text-2xl font-bold text-[#E5E5E5] mb-3">The Paradox</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3">
<strong class="text-[#34D399]">Traditional Approach:</strong>
                                Current AR/VR attempts to solve the cognitive mismatch by adding
                                <em>more</em>
                                —more screens, more cameras, more processing power, more weight.
                            </p>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">
<strong class="text-[#34D399]">Our Approach:</strong>
                                We take the opposite path. Instead of tracking the
                                <em>presence</em>
                                of signal (reflections, point clouds), we track the
                                <em class="text-[#34D399]">absence of signal</em>
                                —the acoustic shadow.
                            </p>
</div>
<div class="grid grid-cols-2 gap-3">
<div class="bg-[#555555]/10 p-4 rounded-lg border border-[#555555]/30">
<div class="flex items-center gap-3 mb-3">
<i class="fas fa-plus-circle text-[#555555] text-2xl">
</i>
<h4 class="font-display text-lg font-bold text-[#E5E5E5]">Traditional AR</h4>
</div>
<ul class="space-y-1 text-base text-[#E5E5E5]/70">
<li>• Active emitters + receivers</li>
<li>• Powered gloves/equipment</li>
<li>• Camera-based tracking</li>
<li>• High computational load</li>
<li>• Privacy concerns</li>
<li>• Battery dependent</li>
</ul>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<div class="flex items-center gap-3 mb-3">
<i class="fas fa-minus-circle text-[#34D399] text-2xl">
</i>
<h4 class="font-display text-lg font-bold text-[#E5E5E5]">Cognitive AR</h4>
</div>
<ul class="space-y-1 text-base text-[#E5E5E5]/70">
<li>• Passive absorbers only</li>
<li>• Battery-free glove</li>
<li>• No cameras needed</li>
<li>• O(1) complexity</li>
<li>• Privacy-first design</li>
<li>• Zero power draw</li>
</ul>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<div class="flex items-center gap-4">
<i class="fas fa-yin-yang text-[#34D399] text-3xl">
</i>
<div>
<h4 class="font-display text-xl font-bold text-[#E5E5E5] mb-1">The Radical Exception</h4>
<p class="text-base text-[#E5E5E5]/80">
                                        We destroyed the "structure" of traditional AR with a radical exception:
                                        <strong class="text-[#34D399]">tracking the absence of signal rather than its presence</strong>
                                        .
                                    </p>
</div>
</div>
</div>
</div>
<div class="flex-[45] flex flex-col gap-3">
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">The Philosophy in Action</h3>
<div class="space-y-3">
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-lg font-bold shrink-0">1</div>
<div>
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Identify the Heavy Structure</h4>
<p class="text-base text-[#E5E5E5]/70">Current AR is heavy, expensive, invasive, and battery-dependent.</p>
</div>
</div>
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-lg font-bold shrink-0">2</div>
<div>
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Find the Inversion</h4>
<p class="text-base text-[#E5E5E5]/70">Instead of adding, subtract. Instead of active, go passive.</p>
</div>
</div>
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-lg font-bold shrink-0">3</div>
<div>
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Create the Exception</h4>
<p class="text-base text-[#E5E5E5]/70">Track shadows, not light. The exception kills the inefficient structure.</p>
</div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Concept Origin</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<p class="font-brand text-2xl text-[#34D399] mb-2">copaeks</p>
<p class="text-lg text-[#E5E5E5]/80 leading-relaxed">
<strong>Cognitive Paradox</strong>
<br/>
<strong>Exception Kills Structure</strong>
</p>
</div>
<p class="text-base text-[#E5E5E5]/70 leading-relaxed">
                                This project was born from
                                <strong class="text-[#34D399]">hyperphantasia</strong>
                                —the ability to visualize complex 3D systems with photographic clarity. Traditional interfaces create a bottleneck for spatial cognition.
                            </p>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="font-brand text-xl text-[#E5E5E5] text-center leading-relaxed">
                            "So you can see what I see."
                            <span class="text-[#34D399]">🕶️</span>
</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 6: The Mission & Market Opportunity -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-5">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Mission &amp; Market</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Mission &amp; Market Opportunity</h2>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-2xl font-bold text-[#E5E5E5] mb-3">Our Mission</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3">To build the first <strong class="text-[#34D399]">Cognitive Interface</strong>—a lightweight, biologically-aligned system that lets you <em>externalize</em> your mental models into physical space, manipulate them with your hands, and share them with others.</p>
<div class="space-y-2">
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Externalize Thought:</strong> Transform internal 3D visualization into shared spatial reality</p></div>
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Natural Interaction:</strong> Use hands, gaze, and voice—no menus, no controllers</p></div>
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Collective Cognition:</strong> Enable shared mental models and spatial collaboration</p></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Why Now?</h3>
<div class="flex-1 flex flex-col justify-around">
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">1</div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Hardware Maturation</h4><p class="text-base text-[#E5E5E5]/70">MEMS transducers, micro-LEDs, and NPUs are now cost-effective</p></div></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">2</div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Enterprise Demand</h4><p class="text-base text-[#E5E5E5]/70">45% of Fortune 500 already adopting AR solutions</p></div></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">3</div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Privacy Awareness</h4><p class="text-base text-[#E5E5E5]/70">Users demand camera-free, data-sovereign solutions</p></div></div>
</div>
</div>
</div>
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Global AR Market Growth</h3>
<div id="market-chart" style="width: 100%; height: 220px;"></div>
<p class="text-sm text-[#E5E5E5]/60 mt-2">Source: Grand View Research, 2025</p>
</div>
<div class="grid grid-cols-2 gap-3">
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center"><div class="text-4xl font-bold text-[#34D399] font-display mb-1">$120B</div><p class="text-sm text-[#E5E5E5]/70">2025 Market Size</p></div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center"><div class="text-4xl font-bold text-[#34D399] font-display mb-1">$1.05T</div><p class="text-sm text-[#E5E5E5]/70">2033 Projection</p></div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center"><div class="text-4xl font-bold text-[#34D399] font-display mb-1">29.7%</div><p class="text-sm text-[#E5E5E5]/70">CAGR (2026-33)</p></div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center"><div class="text-4xl font-bold text-[#34D399] font-display mb-1">38%</div><p class="text-sm text-[#E5E5E5]/70">Smart Glasses CAGR</p></div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg">
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-2">Enterprise Adoption</h4>
<p class="text-base text-[#E5E5E5]/80"><strong class="text-[#34D399]">45%</strong> of Fortune 500 companies have integrated AR solutions, driving demand for lightweight, privacy-preserving hardware.</p>
</div>
</div>
</div>
</div>
<script>
                var marketChart = echarts.init(document.getElementById('market-chart'));
                var option = {
                    tooltip: {
                        trigger: 'axis',
                        backgroundColor: '#2A2A2A',
                        borderColor: '#34D399',
                        textStyle: { color: '#E5E5E5', fontSize: 14 }
                    },
                    grid: { left: '12%', right: '8%', bottom: '15%', top: '10%' },
                    xAxis: {
                        type: 'category',
                        data: ['2025', '2026', '2028', '2030', '2033'],
                        axisLabel: { color: '#E5E5E5', fontSize: 14, fontFamily: 'Quattrocento Sans' },
                        axisLine: { lineStyle: { color: '#555555' } }
                    },
                    yAxis: {
                        type: 'value',
                        name: 'USD Billion',
                        nameTextStyle: { color: '#E5E5E5', fontSize: 14, fontFamily: 'Quattrocento Sans' },
                        axisLabel: { color: '#E5E5E5', fontSize: 13, formatter: '${value}B' },
                        axisLine: { lineStyle: { color: '#555555' } },
                        splitLine: { lineStyle: { color: '#555555', type: 'dashed', opacity: 0.3 } }
                    },
                    series: [{
                        data: [120.21, 169.97, 280, 480, 1050.56],
                        type: 'line',
                        smooth: true,
                        lineStyle: { color: '#34D399', width: 3 },
                        itemStyle: { color: '#34D399' },
                        areaStyle: {
                            color: {
                                type: 'linear',
                                x: 0, y: 0, x2: 0, y2: 1,
                                colorStops: [
                                    { offset: 0, color: 'rgba(52, 211, 153, 0.3)' },
                                    { offset: 1, color: 'rgba(52, 211, 153, 0.05)' }
                                ]
                            }
                        },
                        label: {
                            show: true,
                            position: 'top',
                            color: '#34D399',
                            fontSize: 13,
                            fontWeight: 'bold',
                            formatter: '${c}B'
                        }
                    }]
                };
                marketChart.setOption(option);
                window.addEventListener('resize', function() { marketChart.resize(); });
            </script>
</div>
<!-- Slide 7: Chapter 2 -->
<div class="ppt-slide !bg-[#0A0A0A]" type="chapter">
<img alt="Chapter 2" class="absolute inset-0 w-full h-full object-cover opacity-50" src="chapter_acoustic_shadow.png"/>
<div class="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-[#0A0A0A]/85 to-[#0A0A0A]/50"></div>
<div class="relative h-full flex items-center">
<div class="max-w-3xl">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase mb-4 block">Chapter Two</span>
<h2 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.9]">The<br/>Breakthrough</h2>
<div class="w-40 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90">Passive Acoustic Shadow Tracking (PAST)</p>
</div>
</div>
</div>
<!-- Slide 8: The Problem with Current Tracking -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Current Limitations</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Problem with Current Tracking</h2>
</div>
<div class="flex-1 grid grid-cols-3 gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-t-4 border-red-500 flex flex-col">
<div class="flex items-center gap-3 mb-4">
<div class="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
<i class="fas fa-video text-red-500 text-2xl"></i>
</div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Computer Vision</h3>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-red-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Privacy Invasion:</strong> Cameras record everything, creating biometric data risks</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-red-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Power Drain:</strong> Requires 6-12W of continuous processing</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-red-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Lighting Dependency:</strong> Fails in darkness, glare, or low contrast</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-red-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Computational Load:</strong> O(n³) complexity for point-cloud reconstruction</p>
</div>
</div>
<div class="bg-red-500/10 p-3 rounded-lg border border-red-500/30 mt-3">
<p class="text-base text-[#E5E5E5]/70 text-center"><strong class="text-red-400">Critical Issue:</strong> Visual recording is inherent and unavoidable</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-t-4 border-orange-500 flex flex-col">
<div class="flex items-center gap-3 mb-4">
<div class="w-14 h-14 rounded-full bg-orange-500/20 flex items-center justify-center shrink-0">
<i class="fas fa-satellite-dish text-orange-500 text-2xl"></i>
</div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">LiDAR</h3>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-orange-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Expensive:</strong> High component costs limit mass adoption</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-orange-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Heavy:</strong> Adds significant weight to headsets</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-orange-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Limited Precision:</strong> Blind to fine finger movements</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-orange-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Power Hungry:</strong> Active scanning drains batteries</p>
</div>
</div>
<div class="bg-orange-500/10 p-3 rounded-lg border border-orange-500/30 mt-3">
<p class="text-base text-[#E5E5E5]/70 text-center"><strong class="text-orange-400">Critical Issue:</strong> Not suitable for fine hand tracking</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-t-4 border-yellow-500 flex flex-col">
<div class="flex items-center gap-3 mb-4">
<div class="w-14 h-14 rounded-full bg-yellow-500/20 flex items-center justify-center shrink-0">
<i class="fas fa-wave-square text-yellow-500 text-2xl"></i>
</div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Ultrasound ToF</h3>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-yellow-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>High Latency:</strong> Must wait for echoes (&gt;50ms delay)</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-yellow-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Noise Sensitivity:</strong> Fails in factory/industrial environments</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-yellow-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Powered Gloves:</strong> Requires active electronics, batteries, charging</p>
</div>
<div class="flex items-start gap-2">
<i class="fas fa-times-circle text-yellow-500 mt-1 shrink-0"></i>
<p class="text-base text-[#E5E5E5]/80"><strong>Limited Range:</strong> Short effective tracking distance</p>
</div>
</div>
<div class="bg-yellow-500/10 p-3 rounded-lg border border-yellow-500/30 mt-3">
<p class="text-base text-[#E5E5E5]/70 text-center"><strong class="text-yellow-400">Critical Issue:</strong> Round-trip time creates unavoidable lag</p>
</div>
</div>
</div>
</div>
<div class="mt-4 bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<div class="flex items-center gap-4">
<i class="fas fa-lightbulb text-[#34D399] text-3xl"></i>
<p class="text-lg text-[#E5E5E5]/80"><strong class="text-[#34D399]">The Common Thread:</strong> All existing methods track <em>what IS there</em>—reflections, echoes, visual features. They require active emission and reception, creating power, privacy, and latency problems.</p>
</div>
</div>
</div>
</div>
<!-- Slide 9: PAST - The Shadow, Not the Light -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Core Innovation</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">PAST: The Shadow, Not the Light</h2>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[60] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-2xl font-bold text-[#E5E5E5] mb-3">The Inversion Principle</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-4">Instead of tracking <strong>reflections</strong> (what <em>is</em> there), we track the <strong class="text-[#34D399]">absence of acoustic static</strong> (what <em>isn't</em> there).</p>
<div class="grid grid-cols-2 gap-4">
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-broadcast-tower text-[#34D399]"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">The Field</h4></div>
<p class="text-sm text-[#E5E5E5]/70">Glasses emit constant, inaudible ultrasonic "static" (20-40kHz)—like cosmic microwave background, but acoustic.</p>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-hand-paper text-[#34D399]"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">The Absorber</h4></div>
<p class="text-sm text-[#E5E5E5]/70">Passive glove/ring with acoustic metamaterials absorbs this static completely—zero return signal.</p>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-circle text-[#34D399]"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">The Shadow</h4></div>
<p class="text-sm text-[#E5E5E5]/70">To sensors, the hand appears as a "black hole"—a zone of zero return in the ultrasonic field.</p>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-map text-[#34D399]"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">The Insight</h4></div>
<p class="text-sm text-[#E5E5E5]/70">We map the <strong class="text-[#34D399]">contour of the silence</strong>, not the object itself. O(1) complexity vs O(n³).</p>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-5 rounded-lg border border-[#34D399]/30">
<div class="flex items-center gap-4">
<i class="fas fa-bolt text-[#34D399] text-4xl"></i>
<div>
<h4 class="font-display text-xl font-bold text-[#E5E5E5] mb-1">Computational Revolution</h4>
<p class="text-base text-[#E5E5E5]/80">Mapping shadows requires <strong class="text-[#34D399]">O(1) constant-time complexity</strong> versus <strong class="text-[#555555]">O(n³) point-cloud reconstruction</strong>. This is not an optimization—it's a fundamental paradigm shift.</p>
</div>
</div>
</div>
</div>
<div class="flex-[40] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">How It Works</h3>
<div class="space-y-3">
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">1</div>
<div>
<h4 class="font-display text-base font-bold text-[#E5E5E5]">Emit Ultrasonic Field</h4>
<p class="text-sm text-[#E5E5E5]/70">1-2 MEMS transducers in glasses emit constant 20-40kHz static</p>
</div>
</div>
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">2</div>
<div>
<h4 class="font-display text-base font-bold text-[#E5E5E5]">Absorption Creates Shadow</h4>
<p class="text-sm text-[#E5E5E5]/70">Passive metamaterial glove absorbs 99% of incident acoustic energy</p>
</div>
</div>
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">3</div>
<div>
<h4 class="font-display text-base font-bold text-[#E5E5E5]">4-Microphone Array Detects</h4>
<p class="text-sm text-[#E5E5E5]/70">Beamforming array maps the shadow contour in 3D space</p>
</div>
</div>
<div class="flex items-start gap-3">
<div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">4</div>
<div>
<h4 class="font-display text-base font-bold text-[#E5E5E5]">Edge AI Reconstructs</h4>
<p class="text-sm text-[#E5E5E5]/70">Smartphone NPU processes shadow data into hand skeleton</p>
</div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Visual Analogy</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<p class="text-base text-[#E5E5E5]/80 mb-1"><strong class="text-[#555555]">Traditional:</strong> Like using radar to map an airplane</p>
<p class="text-sm text-[#E5E5E5]/60">• Emit pulse, wait for echo, calculate distance</p>
<p class="text-sm text-[#E5E5E5]/60">• High latency, complex computation</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 mb-1"><strong class="text-[#34D399]">PAST:</strong> Like seeing a silhouette against sunset</p>
<p class="text-sm text-[#E5E5E5]/70">• No emission from the object needed</p>
<p class="text-sm text-[#E5E5E5]/70">• Instant, passive, one-way detection</p>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 10: The Physics of Silence -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Scientific Foundation</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Physics of Silence</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">Acoustic Metamaterials &amp; Inverse Scattering</p>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[55] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Acoustic Metamaterials</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-4">Artificially engineered structures that exhibit <strong class="text-[#34D399]">exotic acoustic properties not found in nature</strong>. Research validates near-perfect absorption at target frequencies.</p>
<div class="grid grid-cols-2 gap-3">
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30 text-center">
<div class="text-3xl font-bold text-[#34D399] font-display mb-1">99%</div>
<p class="text-sm text-[#E5E5E5]/70">Absorption Rate</p>
</div>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30 text-center">
<div class="text-3xl font-bold text-[#34D399] font-display mb-1">20-40kHz</div>
<p class="text-sm text-[#E5E5E5]/70">Operating Range</p>
</div>
</div>
<p class="text-sm text-[#E5E5E5]/60 mt-3 italic">Source: Penn State Acoustics Research, 2024</p>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Helmholtz Equation &amp; Born Approximation</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<div class="bg-[#0A0A0A]/60 p-4 rounded-lg font-mono text-sm text-[#34D399]">
                                (∇² + k²)p(r) = -f(r)
                            </div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">The <strong>Helmholtz equation</strong> governs acoustic wave propagation. Using the <strong class="text-[#34D399]">Born Approximation</strong>, we linearize the inverse scattering problem—enabling real-time shadow reconstruction without iterative optimization.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<p class="text-sm text-[#E5E5E5]/80"><strong class="text-[#34D399]">Key Insight:</strong> Mapping a shadow (absence) is mathematically simpler than reconstructing a surface (presence).</p>
</div>
</div>
</div>
</div>
<div class="flex-[45] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Metamaterial Structure</h3>
<img alt="Acoustic Metamaterial" class="w-full h-40 object-contain rounded-lg mb-3" src="https://kimi-web-img.moonshot.cn/img/www.cee.ed.tum.de/e039a67e99c7885821ac19f255b164996c398db2.webp"/>
<p class="text-sm text-[#E5E5E5]/70">Engineered lattice structures create resonant cavities that trap and dissipate acoustic energy through carefully designed geometries.</p>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Performance Characteristics</h3>
<div class="flex-1 flex flex-col justify-around">
<div>
<div class="flex justify-between items-center mb-1">
<span class="text-base text-[#E5E5E5]/80">Sub-millimeter Precision</span>
<span class="text-base text-[#34D399] font-bold">&lt;1mm</span>
</div>
<div class="w-full bg-[#555555]/20 rounded-full h-2">
<div class="bg-[#34D399] h-2 rounded-full" style="width: 95%"></div>
</div>
</div>
<div>
<div class="flex justify-between items-center mb-1">
<span class="text-base text-[#E5E5E5]/80">Update Rate</span>
<span class="text-base text-[#34D399] font-bold">500Hz</span>
</div>
<div class="w-full bg-[#555555]/20 rounded-full h-2">
<div class="bg-[#34D399] h-2 rounded-full" style="width: 100%"></div>
</div>
</div>
<div>
<div class="flex justify-between items-center mb-1">
<span class="text-base text-[#E5E5E5]/80">Latency</span>
<span class="text-base text-[#34D399] font-bold">&lt;10ms</span>
</div>
<div class="w-full bg-[#555555]/20 rounded-full h-2">
<div class="bg-[#34D399] h-2 rounded-full" style="width: 98%"></div>
</div>
</div>
<div>
<div class="flex justify-between items-center mb-1">
<span class="text-base text-[#E5E5E5]/80">Tracking Volume</span>
<span class="text-base text-[#34D399] font-bold">0.5-2m</span>
</div>
<div class="w-full bg-[#555555]/20 rounded-full h-2">
<div class="bg-[#34D399] h-2 rounded-full" style="width: 85%"></div>
</div>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Gaming Mouse Precision</strong> at <strong class="text-[#34D399]">500Hz</strong> using only <strong class="text-[#34D399]">4 microphones</strong></p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 11: PAST Advantages -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-5">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Breakthrough Benefits</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">PAST Advantages</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">Why Shadow Tracking Changes Everything</p>
</div>
<div class="flex-1 grid grid-cols-3 gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-bolt text-[#34D399] text-xl"></i>
</div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5]">Zero Latency</h3>
</div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3 flex-1"><strong class="text-[#34D399]">No waiting for echoes.</strong> One-way detection only—emitters create the field, receivers detect shadows instantly.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<div class="flex justify-between items-center">
<span class="text-base text-[#E5E5E5]/70">PAST Latency</span>
<span class="text-xl font-bold text-[#34D399] font-display">&lt;10ms</span>
</div>
<div class="flex justify-between items-center mt-1">
<span class="text-base text-[#E5E5E5]/70">Ultrasound ToF</span>
<span class="text-xl font-bold text-[#555555] font-display">&gt;50ms</span>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-volume-up text-[#34D399] text-xl"></i>
</div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5]">Noise Immunity</h3>
</div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3 flex-1"><strong class="text-[#34D399]">Factory noise helps rather than hurts.</strong> Ambient sound increases the contrast of the shadow against the acoustic background.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Counter-Intuitive:</strong> Louder environments = <strong class="text-[#34D399]">Better tracking</strong></p>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-shield-alt text-[#34D399] text-xl"></i>
</div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5]">Privacy-First</h3>
</div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3 flex-1"><strong class="text-[#34D399]">No cameras, no biometric data, no visual recording.</strong> Only acoustic shadows—completely anonymous by design.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<div class="space-y-1 text-base text-[#E5E5E5]/70">
<div class="flex items-center gap-2"><i class="fas fa-check text-[#34D399]"></i><span>No camera hardware</span></div>
<div class="flex items-center gap-2"><i class="fas fa-check text-[#34D399]"></i><span>No facial recognition</span></div>
<div class="flex items-center gap-2"><i class="fas fa-check text-[#34D399]"></i><span>No data harvesting</span></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-battery-full text-[#34D399] text-xl"></i>
</div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5]">Battery-Free</h3>
</div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3 flex-1"><strong class="text-[#34D399]">The glove is completely passive.</strong> No electronics, no charging, no batteries—just engineered metamaterials absorbing sound.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<div class="flex justify-between items-center">
<span class="text-base text-[#E5E5E5]/70">Power Draw</span>
<span class="text-xl font-bold text-[#34D399] font-display">0W</span>
</div>
<div class="flex justify-between items-center mt-1">
<span class="text-base text-[#E5E5E5]/70">Active Gloves</span>
<span class="text-xl font-bold text-[#555555] font-display">2-5W</span>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-crosshairs text-[#34D399] text-xl"></i>
</div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5]">Infinite Precision</h3>
</div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3 flex-1"><strong class="text-[#34D399]">Sub-millimeter tracking at 500Hz</strong> using only 4 microphones. Gaming mouse precision for hand tracking.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<div class="grid grid-cols-2 gap-2 text-center">
<div><div class="text-xl font-bold text-[#34D399] font-display">&lt;1mm</div><p class="text-xs text-[#E5E5E5]/70">Precision</p></div>
<div><div class="text-xl font-bold text-[#34D399] font-display">500Hz</div><p class="text-xs text-[#E5E5E5]/70">Update Rate</p></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center shrink-0">
<i class="fas fa-microchip text-[#34D399] text-xl"></i>
</div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5]">Minimal Hardware</h3>
</div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3 flex-1"><strong class="text-[#34D399]">Simple, cost-effective components.</strong> 1-2 MEMS emitters, 4 microphones, passive glove—no complex optics.</p>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30">
<div class="space-y-1 text-base text-[#E5E5E5]/70">
<div class="flex justify-between"><span>Emitters:</span><span class="text-[#34D399] font-bold">1-2</span></div>
<div class="flex justify-between"><span>Microphones:</span><span class="text-[#34D399] font-bold">4+</span></div>
<div class="flex justify-between"><span>Glove Cost:</span><span class="text-[#34D399] font-bold">$5-10</span></div>
</div>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 12: Chapter 3 -->
<div class="ppt-slide !bg-[#0A0A0A]" type="chapter">
<img alt="Chapter 3" class="absolute inset-0 w-full h-full object-cover opacity-40" src="https://kimi-web-img.moonshot.cn/img/platform.theverge.com/0ed5a2160f30156725507beba4f9622ebda5139a.jpg"/>
<div class="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-[#0A0A0A]/90 to-[#0A0A0A]/60"></div>
<div class="relative h-full flex items-center">
<div class="max-w-3xl">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase mb-4 block">Chapter Three</span>
<h2 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.9]">System<br/>Architecture</h2>
<div class="w-40 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90">The Hardware Trinity &amp; Scalability Layers</p>
</div>
</div>
</div>
<!-- Slide 13: Hardware Trinity -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Core Components</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Hardware Trinity: The &lt;50g Stack</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">We reject the "walled garden" approach. Our stack uses devices you already own.</p>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[60] flex flex-col gap-4">
<div class="grid grid-cols-3 gap-3">
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg border-t-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-2 mb-2">
<i class="fas fa-glasses text-[#34D399] text-xl"></i>
<h3 class="font-display text-lg font-bold text-[#E5E5E5]">Retinal Glasses</h3>
</div>
<p class="text-sm text-[#E5E5E5]/80 mb-2 flex-1">Micro-LED/laser projection directly to retina. No screens, no focal distance issues.</p>
<div class="space-y-1 text-sm">
<div class="flex justify-between text-[#E5E5E5]/70"><span>Cost:</span><span class="text-[#34D399] font-bold">$50-200</span></div>
<div class="flex justify-between text-[#E5E5E5]/70"><span>Power:</span><span class="text-[#34D399] font-bold">&lt;0.5W</span></div>
<div class="flex justify-between text-[#E5E5E5]/70"><span>Weight:</span><span class="text-[#34D399] font-bold">&lt;30g</span></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg border-t-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-2 mb-2">
<i class="fas fa-hand-paper text-[#34D399] text-xl"></i>
<h3 class="font-display text-lg font-bold text-[#E5E5E5]">Passive Glove</h3>
</div>
<p class="text-sm text-[#E5E5E5]/80 mb-2 flex-1">Acoustic shadow generator with metamaterial absorbers. Completely passive.</p>
<div class="space-y-1 text-sm">
<div class="flex justify-between text-[#E5E5E5]/70"><span>Cost:</span><span class="text-[#34D399] font-bold">$5-10</span></div>
<div class="flex justify-between text-[#E5E5E5]/70"><span>Power:</span><span class="text-[#34D399] font-bold">0W</span></div>
<div class="flex justify-between text-[#E5E5E5]/70"><span>Tracking:</span><span class="text-[#34D399] font-bold">10-point</span></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg border-t-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-2 mb-2">
<i class="fas fa-mobile-alt text-[#34D399] text-xl"></i>
<h3 class="font-display text-lg font-bold text-[#E5E5E5]">Smartphone</h3>
</div>
<p class="text-sm text-[#E5E5E5]/80 mb-2 flex-1">Edge AI processing, ultrasound emission/reception, payment rails.</p>
<div class="space-y-1 text-sm">
<div class="flex justify-between text-[#E5E5E5]/70"><span>Cost:</span><span class="text-[#34D399] font-bold">$0</span></div>
<div class="flex justify-between text-[#E5E5E5]/70"><span>Power:</span><span class="text-[#34D399] font-bold">2-3W</span></div>
<div class="flex justify-between text-[#E5E5E5]/70"><span>Location:</span><span class="text-[#34D399] font-bold">Pocket</span></div>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<div class="flex items-center justify-around">
<div class="text-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-1">&lt;30g</div>
<p class="text-sm text-[#E5E5E5]/70">Head Weight</p>
</div>
<div class="w-px h-12 bg-[#34D399]/30"></div>
<div class="text-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-1">&lt;50g</div>
<p class="text-sm text-[#E5E5E5]/70">Total System</p>
</div>
<div class="w-px h-12 bg-[#34D399]/30"></div>
<div class="text-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-1">&lt;$250</div>
<p class="text-sm text-[#E5E5E5]/70">Total Cost</p>
</div>
<div class="w-px h-12 bg-[#34D399]/30"></div>
<div class="text-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-1">&lt;3W</div>
<p class="text-sm text-[#E5E5E5]/70">Total Power</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg flex-1 flex flex-col justify-center">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Comparison: Apple Vision Pro vs Cognitive AR</h3>
<div class="grid grid-cols-2 gap-4">
<div class="space-y-2">
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Head Weight</span><span class="text-[#555555] font-bold">600-650g</span></div>
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Total Cost</span><span class="text-[#555555] font-bold">$3,499</span></div>
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Power Draw</span><span class="text-[#555555] font-bold">12-15W</span></div>
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Battery Life</span><span class="text-[#555555] font-bold">2-4 hours</span></div>
</div>
<div class="space-y-2">
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Head Weight</span><span class="text-[#34D399] font-bold">&lt;30g</span></div>
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Total Cost</span><span class="text-[#34D399] font-bold">&lt;$250</span></div>
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Power Draw</span><span class="text-[#34D399] font-bold">&lt;3W</span></div>
<div class="flex justify-between items-center text-base"><span class="text-[#E5E5E5]/70">Battery Life</span><span class="text-[#34D399] font-bold">All day</span></div>
</div>
</div>
</div>
</div>
<div class="flex-[40] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">System Flow</h3>
<div class="space-y-3">
<div class="flex items-center gap-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-mobile-alt"></i></div>
<i class="fas fa-arrow-right text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg"><p class="text-sm text-[#E5E5E5]/80"><strong>1. Phone emits</strong> ultrasonic static via glasses</p></div>
</div>
<div class="flex items-center gap-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-hand-paper"></i></div>
<i class="fas fa-arrow-right text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg"><p class="text-sm text-[#E5E5E5]/80"><strong>2. Glove absorbs</strong> creating acoustic shadow</p></div>
</div>
<div class="flex items-center gap-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-microphone"></i></div>
<i class="fas fa-arrow-right text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg"><p class="text-sm text-[#E5E5E5]/80"><strong>3. Microphones detect</strong> shadow contour</p></div>
</div>
<div class="flex items-center gap-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-microchip"></i></div>
<i class="fas fa-arrow-right text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg"><p class="text-sm text-[#E5E5E5]/80"><strong>4. NPU processes</strong> into hand tracking data</p></div>
</div>
<div class="flex items-center gap-3">
<div class="w-12 h-12 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-glasses"></i></div>
<i class="fas fa-arrow-right text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg"><p class="text-sm text-[#E5E5E5]/80"><strong>5. Glasses project</strong> AR overlay to retina</p></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Optional: PC Streaming</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<p class="text-base text-[#E5E5E5]/80">For heavy compute tasks (Blender, Unreal Engine), the phone acts as a thin client streaming from existing PC.</p>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80"><strong class="text-[#34D399]">Use Case:</strong> 3D modeling in AR with full desktop GPU power</p>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Bring Your Own Device</strong> philosophy—no hardware lock-in</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 14: Retinal Projection -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Display Technology</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Retinal Projection: Focus-Free Display</h2>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[55] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Direct Retinal Projection (DRP)</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-4">A more experimental approach that beams light <strong class="text-[#34D399]">directly onto the retina</strong>, effectively drawing the image right onto the eye itself. This technology promises incredibly sharp images regardless of the user's eyesight.</p>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 mb-4">
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-2">Why DRP Is Fundamentally Focus-Free</h4>
<p class="text-base text-[#E5E5E5]/80">DRP sidesteps focal plane rendering. Instead of forming an intermediate image in space for the eye to focus on, DRP projects a modulated laser beam <strong class="text-[#34D399]">directly onto the retina</strong> using MEMS mirrors.</p>
</div>
<div class="grid grid-cols-2 gap-3">
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-bullseye text-[#34D399]"></i><h4 class="font-display text-base font-bold text-[#E5E5E5]">Always In Focus</h4></div>
<p class="text-sm text-[#E5E5E5]/70">Images always perceived in focus, regardless of eye accommodation.</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-eye-slash text-[#34D399]"></i><h4 class="font-display text-base font-bold text-[#E5E5E5]">No VAC</h4></div>
<p class="text-sm text-[#E5E5E5]/70">Eliminates vergence-accommodation conflict (eye strain).</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-bolt text-[#34D399]"></i><h4 class="font-display text-base font-bold text-[#E5E5E5]">Low Power</h4></div>
<p class="text-sm text-[#E5E5E5]/70">TDK's thin-film lithium niobate: <strong class="text-[#34D399]">1/4 power</strong> vs conventional.</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex items-center gap-2 mb-2"><i class="fas fa-expand text-[#34D399]"></i><h4 class="font-display text-base font-bold text-[#E5E5E5]">Large FOV</h4></div>
<p class="text-sm text-[#E5E5E5]/70">40-60° diagonal, sufficient for cognitive tasks.</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">The Technology Stack</h3>
<div class="space-y-2">
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">1</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5]">RGB Laser Sources</h4><p class="text-sm text-[#E5E5E5]/70">Red (638nm), green (520nm), blue (455nm) lasers for full color.</p></div></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">2</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5]">Photonic Integration</h4><p class="text-sm text-[#E5E5E5]/70">Thin-film lithium niobate (TFLN) couples colors with high efficiency.</p></div></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">3</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5]">MEMS Beam Scanning</h4><p class="text-sm text-[#E5E5E5]/70">Microelectromechanical mirror raster-scans laser across retina.</p></div></div>
</div>
</div>
</div>
<div class="flex-[45] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">How DRP Works</h3>
<img alt="Retinal Projection" class="w-full h-48 object-contain rounded-lg mb-3" src="https://kimi-web-img.moonshot.cn/img/i0.wp.com/dc298aa8a299ba5eea441721648c6144acab26bb.png"/>
<p class="text-sm text-[#E5E5E5]/70">Laser beams enter the eye and scan directly onto the retina, bypassing the need for the eye's lens to focus.</p>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Technical Specifications</h3>
<div class="flex-1 flex flex-col justify-around">
<div>
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Display Type</span><span class="text-base text-[#34D399] font-bold">Micro-LED / Laser</span></div>
<div class="w-full bg-[#555555]/20 rounded-full h-2"><div class="bg-[#34D399] h-2 rounded-full" style="width: 100%"></div></div>
</div>
<div>
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Focus</span><span class="text-base text-[#34D399] font-bold">Infinite (Retinal)</span></div>
<div class="w-full bg-[#555555]/20 rounded-full h-2"><div class="bg-[#34D399] h-2 rounded-full" style="width: 100%"></div></div>
</div>
<div>
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Brightness</span><span class="text-base text-[#34D399] font-bold">200-1000 nits</span></div>
<div class="w-full bg-[#555555]/20 rounded-full h-2"><div class="bg-[#34D399] h-2 rounded-full" style="width: 90%"></div></div>
</div>
<div>
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Field of View</span><span class="text-base text-[#34D399] font-bold">40°-60° diagonal</span></div>
<div class="w-full bg-[#555555]/20 rounded-full h-2"><div class="bg-[#34D399] h-2 rounded-full" style="width: 75%"></div></div>
</div>
<div>
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Power Consumption</span><span class="text-base text-[#34D399] font-bold">&lt;0.5W</span></div>
<div class="w-full bg-[#555555]/20 rounded-full h-2"><div class="bg-[#34D399] h-2 rounded-full" style="width: 25%"></div></div>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">No Eye Strain:</strong> Users can wear glasses all day without fatigue</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 15: Four Scalability Layers -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Progressive Enhancement</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Four Scalability Layers</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">The system grows with the user, from basic overlays to neural integration</p>
</div>
<div class="flex-1 grid grid-cols-2 gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">L1</div>
<div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Basic (Casual)</h3>
<p class="text-sm text-[#E5E5E5]/60">Entry-Level Experience</p>
</div>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Simple retinal overlays (subtitles, navigation arrows)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Smartphone processing only (NPU inference)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Single-point ring tracking (index finger)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Basic voice commands (local Whisper)</p></div>
</div>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30 mt-3">
<p class="text-base text-[#E5E5E5]/80"><strong>Use Cases:</strong> Daily navigation, real-time translation, notification display</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">L2</div>
<div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Intermediate (Creator)</h3>
<p class="text-sm text-[#E5E5E5]/60">Professional Workflows</p>
</div>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">3D modeling in AR (Blender workflows)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">PC streaming for heavy rendering (Unreal Engine)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Full glove tracking (10-point hand skeleton)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Surface anchoring API (persistent AR objects)</p></div>
</div>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30 mt-3">
<p class="text-base text-[#E5E5E5]/80"><strong>Use Cases:</strong> Industrial design, architecture, 3D art creation</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">L3</div>
<div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Advanced (Pro/BCI)</h3>
<p class="text-sm text-[#E5E5E5]/60">Neural Integration</p>
</div>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Neuralink/Kernel integration for thought-based control</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Haptic feedback in glove (piezo resistors)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Shared spatial workspaces (multi-user collaboration)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Advanced AI models (Llama-70B, multimodal)</p></div>
</div>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30 mt-3">
<p class="text-base text-[#E5E5E5]/80"><strong>Use Cases:</strong> Medical surgery, high-precision manufacturing, research</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3">
<div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-2xl font-bold shrink-0">L4</div>
<div>
<h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Cultural (Network)</h3>
<p class="text-sm text-[#E5E5E5]/60">Collective Cognition</p>
</div>
</div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Shared mental visualizations (think it, they see it)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Spatial social networks (persistent AR worlds)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Collective cognition environments (group problem-solving)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Global knowledge graphs (spatial Wikipedia)</p></div>
</div>
<div class="bg-[#34D399]/10 p-3 rounded-lg border border-[#34D399]/30 mt-3">
<p class="text-base text-[#E5E5E5]/80"><strong>Use Cases:</strong> Education, collaborative research, social interaction</p>
</div>
</div>
</div>
</div>
<div class="mt-4 bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<div class="flex items-center gap-4">
<i class="fas fa-layer-group text-[#34D399] text-3xl"></i>
<p class="text-lg text-[#E5E5E5]/80"><strong class="text-[#34D399]">Modular Progression:</strong> Users start at Layer 1 and upgrade organically. No forced obsolescence—each layer builds on the previous infrastructure.</p>
</div>
</div>
</div>
</div>
<!-- Slide 16: Intent-Based Activation -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Interaction Design</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Intent-Based Activation</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">We do not use menus. The system interprets intention via multi-modal fusion.</p>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[60] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">The Four Modalities</h3>
<div class="grid grid-cols-2 gap-3">
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-3 mb-2"><i class="fas fa-eye text-[#34D399] text-xl"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Gaze</h4></div>
<p class="text-sm text-[#E5E5E5]/70 mb-2">What are you looking at?</p>
<div class="bg-[#34D399]/10 p-2 rounded text-sm text-[#E5E5E5]/80">Retinal tracking + scene analysis</div>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-3 mb-2"><i class="fas fa-hand-paper text-[#34D399] text-xl"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Gesture</h4></div>
<p class="text-sm text-[#E5E5E5]/70 mb-2">What is your hand doing?</p>
<div class="bg-[#34D399]/10 p-2 rounded text-sm text-[#E5E5E5]/80">Ultrasound tracking (PAST)</div>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-3 mb-2"><i class="fas fa-microphone text-[#34D399] text-xl"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Voice</h4></div>
<p class="text-sm text-[#E5E5E5]/70 mb-2">What are you saying?</p>
<div class="bg-[#34D399]/10 p-2 rounded text-sm text-[#E5E5E5]/80">Local LLM processing (Whisper)</div>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<div class="flex items-center gap-3 mb-2"><i class="fas fa-map-marker-alt text-[#34D399] text-xl"></i><h4 class="font-display text-lg font-bold text-[#E5E5E5]">Context</h4></div>
<p class="text-sm text-[#E5E5E5]/70 mb-2">Where are you?</p>
<div class="bg-[#34D399]/10 p-2 rounded text-sm text-[#E5E5E5]/80">GPS, time, activity recognition</div>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-5 rounded-lg border border-[#34D399]/30">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Example: Weather Query</h3>
<div class="flex items-center gap-3 mb-3">
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fas fa-eye text-[#34D399] text-xl mb-1"></i><p class="text-sm text-[#E5E5E5]/80">Looking at window</p></div>
<i class="fas fa-plus text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fas fa-microphone text-[#34D399] text-xl mb-1"></i><p class="text-sm text-[#E5E5E5]/80">Saying "weather"</p></div>
<i class="fas fa-plus text-[#34D399]"></i>
<div class="flex-1 bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fas fa-hand-paper text-[#34D399] text-xl mb-1"></i><p class="text-sm text-[#E5E5E5]/80">Slight hand raise</p></div>
</div>
<div class="bg-[#0A0A0A]/60 p-3 rounded-lg">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Result:</strong> Weather overlay appears <em>on that specific window</em>, not in your face</p>
</div>
</div>
</div>
<div class="flex-[40] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">Why No Menus?</h3>
<div class="space-y-3">
<div class="flex items-start gap-3"><i class="fas fa-brain text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Cognitive Load:</strong> Menus require working memory and visual search</p></div>
<div class="flex items-start gap-3"><i class="fas fa-hand-paper text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Natural Interaction:</strong> Humans communicate through gaze, gesture, and speech</p></div>
<div class="flex items-start gap-3"><i class="fas fa-bolt text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Speed:</strong> Intent recognition is faster than menu navigation</p></div>
<div class="flex items-start gap-3"><i class="fas fa-infinity text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Infinite Commands:</strong> Combinatorial explosion of intent possibilities</p></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">AI Processing Stack</h3>
<div class="flex-1 flex flex-col justify-center gap-3">
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Local Models</span><span class="text-sm text-[#34D399]">Llama-3B, Whisper</span></div>
<p class="text-sm text-[#E5E5E5]/60">Edge-optimized, no cloud dependency</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Inference</span><span class="text-sm text-[#34D399]">4-bit quantization</span></div>
<p class="text-sm text-[#E5E5E5]/60">Runs on smartphone NPU</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><span class="text-base text-[#E5E5E5]/80">Privacy</span><span class="text-sm text-[#34D399]">Federated learning</span></div>
<p class="text-sm text-[#E5E5E5]/60">Raw data never leaves device</p>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">The Interface Disappears</strong> — You simply <em>act naturally</em></p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 17: Chapter 4 -->
<div class="ppt-slide !bg-[#0A0A0A]" type="chapter">
<img alt="Chapter 4" class="absolute inset-0 w-full h-full object-cover opacity-40" src="https://kimi-web-img.moonshot.cn/img/static.vecteezy.com/f1a16bc920f2560e1c699720b9528698f931425c.jpg"/>
<div class="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-[#0A0A0A]/90 to-[#0A0A0A]/60"></div>
<div class="relative h-full flex items-center">
<div class="max-w-3xl">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase mb-4 block">Chapter Four</span>
<h2 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.9]">APP_CENTER &amp;<br/>Economic Layer</h2>
<div class="w-40 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90">The Independent Hub &amp; Capitalism 2.0</p>
</div>
</div>
</div>
<!-- Slide 18: APP_CENTER -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Software Platform</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">APP_CENTER: Cross-Platform Freedom</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">The Problem: Current AR is fragmented. Each is a jail. The Solution: APP_CENTER is a cross-platform, OS-agnostic application hub.</p>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[55] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Key Features</h3>
<div class="space-y-3">
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-cubes"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Modular Installation</h4><p class="text-base text-[#E5E5E5]/70">Install only the modules you need (Manufacturing, Gaming, CCA-Economy, Education).</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-building"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Corporate Profiles</h4><p class="text-base text-[#E5E5E5]/70">Enterprises (like IFF) can deploy custom profiles without touching user data.</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-code-branch"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Workshop Economy</h4><p class="text-base text-[#E5E5E5]/70">Developers build modules; users install via GitHub-style repositories.</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-lock-open"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Zero Lock-in</h4><p class="text-base text-[#E5E5E5]/70">Your data stays on your phone. Always. No cloud dependency.</p></div></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-4 rounded-lg">
<h3 class="font-display text-lg font-bold text-[#E5E5E5] mb-3">Supported Platforms</h3>
<div class="grid grid-cols-5 gap-2">
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fab fa-android text-[#34D399] text-2xl mb-1"></i><p class="text-sm text-[#E5E5E5]/70">Android</p></div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fab fa-apple text-[#34D399] text-2xl mb-1"></i><p class="text-sm text-[#E5E5E5]/70">iOS</p></div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fab fa-windows text-[#34D399] text-2xl mb-1"></i><p class="text-sm text-[#E5E5E5]/70">Windows</p></div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fab fa-linux text-[#34D399] text-2xl mb-1"></i><p class="text-sm text-[#E5E5E5]/70">Linux</p></div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg text-center"><i class="fab fa-chrome text-[#34D399] text-2xl mb-1"></i><p class="text-sm text-[#E5E5E5]/70">Web</p></div>
</div>
</div>
</div>
<div class="flex-[45] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Integration Example</h3>
<div class="bg-[#0A0A0A]/60 p-4 rounded-lg font-mono text-sm text-[#34D399]">
<p>profile: industrial_manufacturing</p>
<p>modules:</p>
<p>  - assembly_guides: v2.1</p>
<p>  - metric_overlays: v1.5</p>
<p>  - cca_economy: disabled</p>
<p>network: vpn_corporate_secure</p>
</div>
<p class="text-sm text-[#E5E5E5]/60 mt-3">YAML configuration enables enterprise deployment with module-level control.</p>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Philosophy</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">"The AR glasses are a <strong class="text-[#34D399]">peripheral</strong>, not a platform. Your phone is the platform. Your data stays on your device."</p>
</div>
<p class="text-base text-[#E5E5E5]/70">This inverts the Apple/Meta model where the headset is the platform and you're locked into their ecosystem.</p>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">No Walled Gardens</strong> — True interoperability</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 19: Contextual Consent Ads (CCA) -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Economic Model</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Contextual Consent Ads (CCA)</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">An ethical advertising protocol that respects cognitive property rights</p>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#555555]/10 p-5 rounded-lg border border-[#555555]/30">
<div class="flex items-center gap-3 mb-4"><i class="fas fa-times-circle text-red-500 text-2xl"></i><h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Traditional Model</h3></div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-4"><strong class="text-red-400">"We steal your attention and sell it"</strong></p>
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-minus text-red-500 mt-1"></i><p class="text-base text-[#E5E5E5]/70">Intrusive pop-ups and banners</p></div>
<div class="flex items-start gap-2"><i class="fas fa-minus text-red-500 mt-1"></i><p class="text-base text-[#E5E5E5]/70">Behavioral tracking across sites</p></div>
<div class="flex items-start gap-2"><i class="fas fa-minus text-red-500 mt-1"></i><p class="text-base text-[#E5E5E5]/70">Biometric data harvesting</p></div>
<div class="flex items-start gap-2"><i class="fas fa-minus text-red-500 mt-1"></i><p class="text-base text-[#E5E5E5]/70">No user compensation</p></div>
<div class="flex items-start gap-2"><i class="fas fa-minus text-red-500 mt-1"></i><p class="text-base text-[#E5E5E5]/70">Adversarial relationship</p></div>
</div>
</div>
<div class="bg-[#34D399]/10 p-5 rounded-lg border border-[#34D399]/30 flex-1 flex flex-col">
<div class="flex items-center gap-3 mb-4"><i class="fas fa-check-circle text-[#34D399] text-2xl"></i><h3 class="font-display text-2xl font-bold text-[#E5E5E5]">CCA Model</h3></div>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-4"><strong class="text-[#34D399]">"You lease your attention and get paid directly"</strong></p>
<div class="space-y-2 flex-1">
<div class="flex items-start gap-2"><i class="fas fa-plus text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/70">Surface-anchored ads (walls, windows)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-plus text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/70">"Dot" invitation system—user chooses to engage</p></div>
<div class="flex items-start gap-2"><i class="fas fa-plus text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/70">Zero tracking—only "ad viewed" verified</p></div>
<div class="flex items-start gap-2"><i class="fas fa-plus text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/70">Micro-payments to user (crypto/fiat)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-plus text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/70">Collaborative relationship</p></div>
</div>
</div>
</div>
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">How CCA Works</h3>
<div class="space-y-3">
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">1</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Surface Anchoring</h4><p class="text-sm text-[#E5E5E5]/70">Ads anchored to real surfaces—walls, windows, tables—not floating interruptions.</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">2</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Dot Invitation</h4><n<p class="text-sm text-[#E5E5E5]/70">User sees subtle marker, chooses to engage, earns micro-payments.</n</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">3</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Zero Tracking</h4><p class="text-sm text-[#E5E5E5]/70">Only "an ad was viewed" is verified—not "who viewed it."</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-base font-bold shrink-0">4</div><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Direct Payment</h4><p class="text-sm text-[#E5E5E5]/70">User receives crypto/fiat micropayments for attention.</p></div></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Cognitive Property Rights</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">Your <strong class="text-[#34D399]">thoughts, gaze, and attention</strong> are your property. Technology should <em>rent</em> them, never <em>steal</em> them.</p>
</div>
<p class="text-base text-[#E5E5E5]/70">CCA creates a fair marketplace for attention where users are compensated for their most valuable resource.</p>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Capitalism 2.0:</strong> Value flows to attention providers</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 20: Chapter 5 -->
<div class="ppt-slide !bg-[#0A0A0A]" type="chapter">
<img alt="Chapter 5" class="absolute inset-0 w-full h-full object-cover opacity-50" src="https://kimi-web-img.moonshot.cn/img/static.vecteezy.com/d4c0b31c2966aa0b68062dbeee423f0a1e528b8e.jpg"/>
<div class="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-[#0A0A0A]/85 to-[#0A0A0A]/50"></div>
<div class="relative h-full flex items-center">
<div class="max-w-3xl">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase mb-4 block">Chapter Five</span>
<h2 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.9]">Use Cases &amp;<br/>Applications</h2>
<div class="w-40 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90">From Factory to Living Room</p>
</div>
</div>
</div>
<!-- Slide 21: Industrial & Manufacturing -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Enterprise Applications</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Industrial &amp; Manufacturing</h2>
<p class="text-lg text-[#E5E5E5]/70 mt-1">IFF Validation — Proven ROI in Aerospace &amp; Industrial Settings</p>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[55] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">The Scenario</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-4"><strong class="text-[#34D399]">Technician assembling a complex chemical processing unit.</strong></p>
<div class="grid grid-cols-2 gap-3">
<div class="bg-[#555555]/10 p-4 rounded-lg border border-[#555555]/30">
<h4 class="font-display text-base font-bold text-[#E5E5E5] mb-2">Traditional</h4>
<ul class="space-y-1 text-sm text-[#E5E5E5]/70">
<li>• Stop work, check tablet manual</li>
<li>• Get confused by 2D diagrams</li>
<li>• Make errors, rework required</li>
<li>• Hands leave tools repeatedly</li>
</ul>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<h4 class="font-display text-base font-bold text-[#E5E5E5] mb-2">Cognitive AR</h4>
<ul class="space-y-1 text-sm text-[#E5E5E5]/70">
<li>• Holographic specs anchored to bolt</li>
<li>• 3D overlay shows exact procedure</li>
<li>• Errors corrected in real-time</li>
<li>• Hands never leave tools</li>
</ul>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Validated ROI Metrics</h3>
<div class="flex-1 grid grid-cols-2 gap-3">
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center flex flex-col justify-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-2">30%</div>
<p class="text-base text-[#E5E5E5]/80 font-bold">Productivity Increase</p>
<p class="text-sm text-[#E5E5E5]/60 mt-1">Average across manufacturing</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center flex flex-col justify-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-2">90%</div>
<p class="text-base text-[#E5E5E5]/80 font-bold">Accuracy Improvement</p>
<p class="text-sm text-[#E5E5E5]/60 mt-1">For intricate procedures</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center flex flex-col justify-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-2">70%</div>
<p class="text-base text-[#E5E5E5]/80 font-bold">Training Retention</p>
<p class="text-sm text-[#E5E5E5]/60 mt-1">Higher than traditional methods</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center flex flex-col justify-center">
<div class="text-4xl font-bold text-[#34D399] font-display mb-2">25-75%</div>
<p class="text-base text-[#E5E5E5]/80 font-bold">Error Reduction</p>
<p class="text-sm text-[#E5E5E5]/60 mt-1">Proven in aerospace studies</p>
</div>
</div>
<p class="text-sm text-[#E5E5E5]/60 mt-3">Source: DELMIA Augmented Experience, Aerospace Manufacturing Studies 2025</p>
</div>
</div>
<div class="flex-[45] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Real-World Results</h3>
<div class="space-y-3">
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><h4 class="font-display text-base font-bold text-[#E5E5E5]">Aerospace Sector</h4><span class="text-[#34D399] font-bold text-sm">34% ↑</span></div>
<p class="text-sm text-[#E5E5E5]/70">Assembly speed increase + zero non-conformance for complex parts</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><h4 class="font-display text-base font-bold text-[#E5E5E5]">Commercial Trucks</h4><span class="text-[#34D399] font-bold text-sm">50% ↓</span></div>
<p class="text-sm text-[#E5E5E5]/70">Takt time reduced by half, rework dropped by 80%</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><h4 class="font-display text-base font-bold text-[#E5E5E5]">Latecoere</h4><span class="text-[#34D399] font-bold text-sm">30% ↓</span></div>
<p class="text-sm text-[#E5E5E5]/70">Inspection times cut by up to 30%, rework costs reduced</p>
</div>
<div class="bg-[#0A0A0A]/40 p-3 rounded-lg">
<div class="flex justify-between items-center mb-1"><h4 class="font-display text-base font-bold text-[#E5E5E5]">Safran Aerospace</h4><span class="text-[#34D399] font-bold text-sm">4x ↑</span></div>
<p class="text-sm text-[#E5E5E5]/70">Incoming inspections 4x more efficient, non-quality costs ÷7</p>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Key Advantages</h3>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Hands-Free Operation:</strong> Technicians keep hands on tools</p></div>
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Contextual Guidance:</strong> Instructions anchored to exact components</p></div>
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Real-Time Correction:</strong> Errors caught immediately, not after</p></div>
<div class="flex items-start gap-3"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Privacy-Safe:</strong> No cameras recording factory floor</p></div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 22: Consumer Commerce & Daily Life -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Consumer Applications</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Consumer Commerce &amp; Daily Life</h2>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Commerce Applications</h3>
<div class="space-y-3">
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-2">The Scenario: Buying a Vase</h4>
<div class="grid grid-cols-2 gap-3">
<div>
<p class="text-sm text-[#555555] font-bold mb-1">Traditional</p>
<ul class="space-y-1 text-sm text-[#E5E5E5]/70">
<li>• Look at 2D photo</li>
<li>• Guess if it fits</li>
<li>• Buy, return if wrong</li>
</ul>
</div>
<div>
<p class="text-sm text-[#34D399] font-bold mb-1">Cognitive AR</p>
<ul class="space-y-1 text-sm text-[#E5E5E5]/70">
<li>• Place 3D on table</li>
<li>• Walk around it</li>
<li>• Buy with confidence</li>
</ul>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<h4 class="font-display text-base font-bold text-[#E5E5E5] mb-2">ROI for Retailers</h4>
<div class="grid grid-cols-2 gap-2 text-center">
<div><div class="text-2xl font-bold text-[#34D399] font-display">~0%</div><p class="text-xs text-[#E5E5E5]/70">Return Rates</p></div>
<div><div class="text-2xl font-bold text-[#34D399] font-display">+40%</div><p class="text-xs text-[#E5E5E5]/70">Conversion</p></div>
</div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">BMW Car Configuration</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<p class="text-base text-[#E5E5E5]/80">Configure your car in your driveway. See different colors, wheels, and interiors at 1:1 scale.</p>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80"><strong class="text-[#34D399]">User earns CCA credits</strong> during browsing—attention monetized</p>
</div>
</div>
</div>
</div>
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Daily Life Applications</h3>
<div class="space-y-3">
<div class="flex items-start gap-3"><i class="fas fa-closed-captioning text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Private Subtitles</h4><p class="text-sm text-[#E5E5E5]/70">Real-time translation floating only in your retinal view—not on a screen blocking the speaker.</p></div></div>
<div class="flex items-start gap-3"><i class="fas fa-route text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Navigation</h4><p class="text-sm text-[#E5E5E5]/70">Subtle arrows painted on the sidewalk via AR, not voice commands. Always know where to turn.</p></div></div>
<div class="flex items-start gap-3"><i class="fas fa-users text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Social Memory</h4><p class="text-sm text-[#E5E5E5]/70">"Memory dots" floating above friends' heads with context—how you met, their preferences—visible only to you.</p></div></div>
<div class="flex items-start gap-3"><i class="fas fa-utensils text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Cooking Assistant</h4><p class="text-sm text-[#E5E5E5]/70">Recipes anchored to kitchen counters, timers floating above stoves, ingredient lists in peripheral vision.</p></div></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">The Invisible Assistant</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">AR should be <strong class="text-[#34D399]">invisible until needed</strong>, then disappear when done. No persistent interfaces cluttering your view.</p>
</div>
<p class="text-base text-[#E5E5E5]/70">The system understands context and only shows relevant information at the right moment.</p>
</div>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 23: Education & Creativity -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Learning &amp; Creation</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Education &amp; Creativity</h2>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Education Applications</h3>
<div class="space-y-3">
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-2">Molecular Biology</h4>
<p class="text-sm text-[#E5E5E5]/80 mb-2">Students manipulate a DNA helix with their hands in the classroom.</p>
<div class="bg-[#34D399]/10 p-2 rounded-lg">
<div class="flex justify-between items-center"><span class="text-sm text-[#E5E5E5]/70">Spatial Retention</span><span class="text-xl font-bold text-[#34D399] font-display">3x ↑</span></div>
</div>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-2">Physics &amp; Engineering</h4>
<p class="text-sm text-[#E5E5E5]/80">Visualize electromagnetic fields, fluid dynamics, and structural forces in 3D space.</p>
</div>
<div class="bg-[#0A0A0A]/40 p-4 rounded-lg">
<h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-2">Medical Training</h4>
<p class="text-sm text-[#E5E5E5]/80">Practice surgery on 3D anatomical models overlaid on physical training dummies.</p>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-5 rounded-lg border border-[#34D399]/30 flex-1 flex flex-col justify-center">
<div>
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Pedagogical Impact</h3>
<p class="text-base text-[#E5E5E5]/80 leading-relaxed mb-3">Research shows <strong class="text-[#34D399]">spatial memory retention increases 3x</strong> when learners interact with 3D models versus 2D diagrams.</p>
<div class="space-y-2">
<div class="flex items-center gap-2"><i class="fas fa-brain text-[#34D399]"></i><p class="text-base text-[#E5E5E5]/70">Embodied cognition enhances understanding</p></div>
<div class="flex items-center gap-2"><i class="fas fa-hands text-[#34D399]"></i><p class="text-base text-[#E5E5E5]/70">Kinesthetic learning improves retention</p></div>
<div class="flex items-center gap-2"><i class="fas fa-eye text-[#34D399]"></i><p class="text-base text-[#E5E5E5]/70">Visual-spatial processing fully engaged</p></div>
</div>
</div>
</div>
</div>
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Creative Applications</h3>
<div class="space-y-3">
<div class="flex items-start gap-3"><i class="fas fa-cube text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">3D Sculpting</h4><p class="text-sm text-[#E5E5E5]/70">Sculpt NFTs and 3D models in physical space while seeing your real desk and tools.</p></div></div>
<div class="flex items-start gap-3"><i class="fas fa-paint-brush text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Spatial Painting</h4><p class="text-sm text-[#E5E5E5]/70">Paint in 3D space with virtual brushes, creating immersive art installations.</p></div></div>
<div class="flex items-start gap-3"><i class="fas fa-film text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Storyboarding</h4><p class="text-sm text-[#E5E5E5]/70">Arrange scenes in 3D space, walk through narrative structures physically.</p></div></div>
<div class="flex items-start gap-3"><i class="fas fa-music text-[#34D399] text-xl mt-1"></i><div><h4 class="font-display text-base font-bold text-[#E5E5E5] mb-1">Music Composition</h4><p class="text-sm text-[#E5E5E5]/70">Visualize sound waves and arrange compositions in 3D auditory space.</p></div></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">For Hyperphantasics</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">This project was born from <strong class="text-[#34D399]">hyperphantasia</strong>—the ability to visualize complex 3D systems with photographic clarity in the mind's eye.</p>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 italic">"The Cognitive AR Interface is essentially a prosthetic for imagination—allowing spatial thinkers to externalize their mental models into the shared physical world."</p>
</div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Democratizing 3D Thinking</strong> — Built by a hyperphantasic, for everyone who thinks spatially</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 24: Chapter 6 -->
<div class="ppt-slide !bg-[#0A0A0A]" type="chapter">
<img alt="Chapter 6" class="absolute inset-0 w-full h-full object-cover opacity-40" src="https://kimi-web-img.moonshot.cn/img/thumbs.dreamstime.com/d12c6360e7ff0505693826ddb2570f749916f1c6.jpg"/>
<div class="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-[#0A0A0A]/90 to-[#0A0A0A]/60"></div>
<div class="relative h-full flex items-center">
<div class="max-w-3xl">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase mb-4 block">Chapter Six</span>
<h2 class="font-display text-8xl font-bold text-[#E5E5E5] mb-6 leading-[0.9]">Technical Specs<br/>&amp; Roadmap</h2>
<div class="w-40 h-1 bg-[#34D399] mb-6"></div>
<p class="font-brand text-4xl text-[#E5E5E5]/90">Engineering Reality</p>
</div>
</div>
</div>
<!-- Slide 25: Technical Specifications -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Engineering Details</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Technical Specifications</h2>
</div>
<div class="flex-1 grid grid-cols-3 gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-t-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-4"><i class="fas fa-wave-square text-[#34D399] text-2xl"></i><h3 class="font-display text-xl font-bold text-[#E5E5E5]">Ultrasound Tracking</h3></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Frequency</span><span class="text-base text-[#34D399] font-bold">20-40kHz</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Emitters</span><span class="text-base text-[#34D399] font-bold">1-2 MEMS</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Receivers</span><span class="text-base text-[#34D399] font-bold">4+ mics</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Update Rate</span><span class="text-base text-[#34D399] font-bold">100-500Hz</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Latency</span><span class="text-base text-[#34D399] font-bold">&lt;10ms</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Tracking Volume</span><span class="text-base text-[#34D399] font-bold">0.5-2m</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Precision</span><span class="text-base text-[#34D399] font-bold">&lt;1mm</span></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-t-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-4"><i class="fas fa-glasses text-[#34D399] text-2xl"></i><h3 class="font-display text-xl font-bold text-[#E5E5E5]">Retinal Projection</h3></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Display Type</span><span class="text-base text-[#34D399] font-bold">Micro-LED</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Focus</span><span class="text-base text-[#34D399] font-bold">Infinite</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Brightness</span><span class="text-base text-[#34D399] font-bold">200-1000 nits</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Field of View</span><span class="text-base text-[#34D399] font-bold">40°-60°</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Power Draw</span><span class="text-base text-[#34D399] font-bold">&lt;0.5W</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Weight</span><span class="text-base text-[#34D399] font-bold">&lt;30g</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Cost</span><span class="text-base text-[#34D399] font-bold">$50-200</span></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-t-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-4"><i class="fas fa-microchip text-[#34D399] text-2xl"></i><h3 class="font-display text-xl font-bold text-[#E5E5E5]">AI Processing</h3></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-3">
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Local Models</span><span class="text-base text-[#34D399] font-bold">Llama-3B</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Speech</span><span class="text-base text-[#34D399] font-bold">Whisper</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Inference</span><span class="text-base text-[#34D399] font-bold">4-bit quant</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Hardware</span><span class="text-base text-[#34D399] font-bold">Phone NPU</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Privacy</span><span class="text-base text-[#34D399] font-bold">Federated</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Power Draw</span><span class="text-base text-[#34D399] font-bold">2-3W</span></div>
<div class="flex justify-between items-center"><span class="text-base text-[#E5E5E5]/80">Cost</span><span class="text-base text-[#34D399] font-bold">$0 (existing)</span></div>
</div>
</div>
</div>
</div>
<div class="mt-4 grid grid-cols-4 gap-4">
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center">
<div class="text-3xl font-bold text-[#34D399] font-display mb-1">&lt;50g</div>
<p class="text-sm text-[#E5E5E5]/70">Total System Weight</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center">
<div class="text-3xl font-bold text-[#34D399] font-display mb-1">&lt;$250</div>
<p class="text-sm text-[#E5E5E5]/70">Total System Cost</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center">
<div class="text-3xl font-bold text-[#34D399] font-display mb-1">&lt;3W</div>
<p class="text-sm text-[#E5E5E5]/70">Total Power Draw</p>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30 text-center">
<div class="text-3xl font-bold text-[#34D399] font-display mb-1">&lt;10ms</div>
<p class="text-sm text-[#E5E5E5]/70">Total Latency</p>
</div>
</div>
</div>
</div>
<!-- Slide 26: Development Roadmap -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Timeline</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">Development Roadmap</h2>
</div>
<div class="flex-1 grid grid-cols-2 gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3"><div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-xl font-bold shrink-0">P1</div><div><h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Phase 1: PoC</h3><p class="text-sm text-[#34D399]">Current</p></div></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Mathematical formalization of IAS/PAST</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">System architecture documentation</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">CCA economic model specification</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Prototype ultrasound tracking (Arduino → Python)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-check-circle text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80">Retinal projection simulation (Unity/Unreal)</p></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3"><div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-xl font-bold shrink-0">P2</div><div><h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Phase 2: MVP</h3><p class="text-sm text-[#34D399]">Q3 2026</p></div></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Functional glove prototype (3D printed + foam)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">APP_CENTER alpha (Android/iOS)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Basic retinal overlay demo (weather, subtitles)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">First corporate pilot (IFF manufacturing)</p></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3"><div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-xl font-bold shrink-0">P3</div><div><h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Phase 3: Dev Release</h3><p class="text-sm text-[#34D399]">2027</p></div></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Public SDK for Surface Anchor API</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">CCA testnet (micro-payments live)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Community module marketplace</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Integration with major LLMs (xAI, OpenAI, local)</p></div>
</div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg border-l-4 border-[#34D399] flex flex-col">
<div class="flex items-center gap-3 mb-3"><div class="w-14 h-14 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-display text-xl font-bold shrink-0">P4</div><div><h3 class="font-display text-2xl font-bold text-[#E5E5E5]">Phase 4: Neural</h3><p class="text-sm text-[#34D399]">2028+</p></div></div>
<div class="flex-1 flex flex-col justify-around">
<div class="space-y-2">
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">BCI hooks (Neuralink, Kernel, etc.)</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Thought-to-form direct rendering</p></div>
<div class="flex items-start gap-2"><i class="fas fa-circle text-[#34D399] mt-1 text-xs"></i><p class="text-base text-[#E5E5E5]/80">Shared cognitive spaces (multi-user spatial collaboration)</p></div>
</div>
</div>
</div>
</div>
<div class="mt-4 bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<div class="flex items-center gap-4">
<i class="fas fa-rocket text-[#34D399] text-3xl"></i>
<p class="text-lg text-[#E5E5E5]/80"><strong class="text-[#34D399]">Open Development:</strong> All phases documented on GitHub. Community contributions welcome at every stage.</p>
</div>
</div>
</div>
</div>
<!-- Slide 27: Philosophy & Call to Action -->
<div class="ppt-slide !bg-[#0A0A0A]" type="content">
<div class="h-full flex flex-col">
<div class="mb-4">
<span class="text-sm font-caption tracking-[0.3em] text-[#34D399] uppercase">Join the Movement</span>
<h2 class="font-display text-4xl font-bold text-[#E5E5E5] mt-2">The Philosophy &amp; Call to Action</h2>
</div>
<div class="flex-1 flex gap-5">
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">Core Principles</h3>
<div class="space-y-3">
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-bolt"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Exception Kills Structure</h4><p class="text-base text-[#E5E5E5]/70">If the old way is heavy, expensive, and invasive, <strong class="text-[#34D399]">invert it</strong>.</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-leaf"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Biomimicry</h4><p class="text-base text-[#E5E5E5]/70">Dolphins use echolocation; we use acoustic shadows. <strong class="text-[#34D399]">Nature already solved this.</strong></p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-shield-alt"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Cognitive Sovereignty</h4><n<p class="text-base text-[#E5E5E5]/70">Your thoughts, your gaze, your attention are <strong class="text-[#34D399]">your property</strong>. Technology should rent them, never steal them.</n</p></div></div>
<div class="flex items-start gap-3"><div class="w-10 h-10 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] shrink-0"><i class="fas fa-unlock"></i></div><div><h4 class="font-display text-lg font-bold text-[#E5E5E5] mb-1">Modular Independence</h4><p class="text-base text-[#E5E5E5]/70">No OS lock-in. No hardware lock-in. <strong class="text-[#34D399]">No data lock-in.</strong></p></div></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">Origin Story</h3>
<div class="flex-1 flex flex-col justify-center gap-4">
<p class="text-base text-[#E5E5E5]/80 leading-relaxed">This project was born from <strong class="text-[#34D399]">hyperphantasia</strong>—the ability to visualize complex 3D systems with photographic clarity in the mind's eye.</p>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 italic">"Traditional interfaces create a bottleneck for spatial cognition. The Cognitive AR Interface is a prosthetic for imagination."</p>
</div>
</div>
</div>
</div>
<div class="flex-[50] flex flex-col gap-4">
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-4">We Seek Collaborators</h3>
<p class="text-base text-[#E5E5E5]/80 mb-4">We seek collaborators who understand that <strong class="text-[#34D399]">the interface is the message</strong>:</p>
<div class="space-y-2">
<div class="flex items-start gap-3"><i class="fas fa-microchip text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Hardware Engineers:</strong> MEMS acoustics, retinal projection optics</p></div>
<div class="flex items-start gap-3"><i class="fas fa-brain text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>AI/ML Engineers:</strong> Edge optimization, federated learning, acoustic signal processing</p></div>
<div class="flex items-start gap-3"><i class="fas fa-atom text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Physicists:</strong> Validation of IAS models, cosmological analogies</p></div>
<div class="flex items-start gap-3"><i class="fas fa-balance-scale text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Philosophers/Economists:</strong> Ethical frameworks for attention markets</p></div>
<div class="flex items-start gap-3"><i class="fas fa-industry text-[#34D399] mt-1"></i><p class="text-base text-[#E5E5E5]/80"><strong>Manufacturing Experts:</strong> Real-world validation (IFF network)</p></div>
</div>
</div>
<div class="bg-[#2A2A2A]/40 p-5 rounded-lg flex-1 flex flex-col">
<h3 class="font-display text-xl font-bold text-[#E5E5E5] mb-3">How to Contribute</h3>
<div class="flex-1 flex flex-col justify-center gap-3">
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">1</div><p class="text-base text-[#E5E5E5]/80">Fork this repository</p></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">2</div><p class="text-base text-[#E5E5E5]/80">Read /docs/CONTRIBUTING.md</p></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">3</div><p class="text-base text-[#E5E5E5]/80">Join the discussion in Issues</p></div>
<div class="flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-[#34D399]/20 flex items-center justify-center text-[#34D399] font-bold shrink-0">4</div><p class="text-base text-[#E5E5E5]/80">Submit PRs against develop branch</p></div>
</div>
</div>
<div class="bg-[#34D399]/10 p-4 rounded-lg border border-[#34D399]/30">
<p class="text-base text-[#E5E5E5]/80 text-center"><strong class="text-[#34D399]">Code of Conduct:</strong> Be exceptional. Kill inefficient structures gently but firmly.</p>
</div>
</div>
</div>
</div>
</div>
<!-- Slide 28: Final -->
<div class="ppt-slide !bg-[#0A0A0A]" type="final">
<img alt="Final" class="absolute inset-0 w-full h-full object-cover opacity-50" src="final_shared_cognition.png"/>
<div class="absolute inset-0 bg-gradient-to-br from-[#0A0A0A]/95 via-[#0A0A0A]/80 to-transparent"></div>
<div class="relative h-full flex flex-col justify-center items-center text-center">
<div class="mb-8">
<div class="w-24 h-1 bg-[#34D399] mx-auto mb-6"></div>
<h2 class="font-display text-7xl font-bold text-[#E5E5E5] mb-6 leading-tight">So You Can See<br/>What I See</h2>
<div class="w-24 h-1 bg-[#34D399] mx-auto"></div>
</div>
<div class="max-w-3xl mb-8">
<p class="font-brand text-3xl text-[#E5E5E5]/90 mb-6">This is not a product. It is infrastructure for the next phase of human cognition.</p>
<p class="text-xl text-[#E5E5E5]/70 leading-relaxed">We are not building a metaverse to escape reality; we are building a cognitive interface to <strong class="text-[#34D399]">understand reality better</strong>.</p>
</div>
<div class="grid grid-cols-3 gap-6 max-w-4xl mb-8">
<div class="bg-[#2A2A2A]/60 p-5 rounded-lg backdrop-blur-sm">
<i class="fas fa-map-marker-alt text-[#34D399] text-3xl mb-3"></i>
<p class="text-base text-[#E5E5E5]/80">Built in<br/><strong class="text-[#34D399]">Cuernavaca, Mexico</strong></p>
</div>
<div class="bg-[#2A2A2A]/60 p-5 rounded-lg backdrop-blur-sm">
<i class="fas fa-globe text-[#34D399] text-3xl mb-3"></i>
<p class="text-base text-[#E5E5E5]/80">Licensed to<br/><strong class="text-[#34D399]">the World</strong></p>
</div>
<div class="bg-[#2A2A2A]/60 p-5 rounded-lg backdrop-blur-sm">
<i class="fas fa-code-branch text-[#34D399] text-3xl mb-3"></i>
<p class="text-base text-[#E5E5E5]/80">Open Source<br/><strong class="text-[#34D399]">MIT License</strong></p>
</div>
</div>
<div class="flex items-center gap-6 text-base text-[#E5E5E5]/60">
<div class="flex items-center gap-2"><i class="fab fa-github text-[#34D399]"></i><span>github.com/copaeks/cognitive-interface</span></div>
<div class="flex items-center gap-2"><i class="fas fa-user text-[#34D399]"></i><span>@copaeks</span></div>
</div>
</div>
</div>
</body>
</html>
