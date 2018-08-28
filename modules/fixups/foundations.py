#!/usr/bin/python3

from enum import Enum

class KitStabilityRating(Enum):
	PRIME = 0  # Kit is enterprise-quality
	NEAR_PRIME = 1  # Kit is approaching enterprise-quality
	BETA = 2  # Kit is in beta
	ALPHA = 3  # Kit is in alpha
	DEV = 4  # Kit is newly created and in active development
	CURRENT = 10  # Kit follows Gentoo currrent
	DEPRECATED = 11  # Kit is deprecated/retired


def KitRatingString(kit_enum):
	if kit_enum is KitStabilityRating.PRIME:
		return "prime"
	elif kit_enum is KitStabilityRating.NEAR_PRIME:
		return "near-prime"
	elif kit_enum is KitStabilityRating.BETA:
		return "beta"
	elif kit_enum is KitStabilityRating.ALPHA:
		return "alpha"
	elif kit_enum is KitStabilityRating.DEV:
		return "dev"
	elif kit_enum is KitStabilityRating.CURRENT:
		return "current"
	elif kit_enum is KitStabilityRating.DEPRECATED:
		return "deprecated"

# A kit is generated from:

# 1. a collection of repositories and SHA1 commit to specify a snapshot of each repository to serve as a source for catpkgs,
#    eclasses, licenses. It is also possible to specify a branch name instead of SHA1 (typically 'master') although this
#    shouldn't ever be done for 'prime' branches of kits.

# 1. a selection of catpkgs (ebuilds) that are selected from source repositories. Each kit has a package-set file located
#    in ../package-sets/*-kit relative to this file which contains patterns of catpkgs to select from each source
#    repository and copy into the kit when regenerating it.

# 3. a collection of fix-ups (from the kit-fixups repository) that can be used to replace catpkgs in various kits globally,
#    or in a specific branch of a kit. There is also an option to provide eclasses that get copied globally to each kit,
#    to a particular kit, or to a branch of a particular kit. This is the where we fork ebuilds to fix specific issues.

# When setting up a kit repository, the 'master' branch may used to store an 'unfrozen' kit that just tracks upstream
# Gentoo. Kits are not required to have a master branch -- we only create one if the kit is designed to offer unfrozen
# ebuilds to Funtoo users.	Examples below are: science-kit, games-kit, text-kit, net-kit. These track gentoo.

# If we have a frozen enterprise branch that we are backporting security fixes to only, we want this to be an
# 'x.y-prime' branch. This branch's overlays' source SHA1s are not supposed to change and we will just augment it with
# fix-ups as needed.

# As kits are maintained, the following things may change:
#
# 1. The package-set files may change. This can result in different packages being selected for the kit the next time it
#	 is regenerated by this script. We can add mising packages, decide to move packages to other kits, etc. This script
#	 takes care of ensuring that all necessary eclasses and licenses are included when the kit is regenerated.
#
# 2. The fix-ups may change. This allows us to choose to 'fork' various ebuilds that we may need to fix, while keeping
#	 our changes separate from the source packages. We can also choose to unfork packages.
#
# 3. Kits can be added or removed.
#
# 4. Kit branches can be created, or alternatively deprecated. We need a system for gracefully deprecating a kit that does
#	 not involve deleting the branch. A user may decide to continue using the branch even if it has been deprecated.
#
# 5. Kits can be tagged by Funtoo as being mandatory or optional. Typically, most kits will be mandatory but some effort
#	 will be made as we progress to make things like the games-kit or the science-kit optional.
#
# HOW KITS ARE GENERATED

# Currently, kits are regenerated in a particluar order, such as: "first, core-kit, then security-kit, then perl-kit",
# etc. This script keeps a running list of catpkgs that are inserted into each kit. Once a catpkg is inserted into a
# kit, it is not available to be inserted into successive kits. This design is intended to prevent multiple copies of
# catpkgs existing in multiple kits in parallel that are designed to work together as a set. At the end of kit
# generation, this master list of inserted catpkgs is used to prune the 'nokit' repository of catpkgs, so that 'nokit'
# contains the set of all ebuilds that were not inserted into kits.

# Next release is 1.2-prime and will be based on a 'master' snapshot until it is near release, at which point the
# tree will be frozen.

# 1.2 RELEASE
# =================================================================================
#
# Roadmap (compressed development schedule)
#
# 1. Development starts                                                            December 28, 2017
# 1a. Addition of python-modules-kit and perl-modules-kit (for 1.1+)               January 1, 2018
# 2. Alpha release (best attempt to get everything functioning)                    January 4, 2018
# 3. Beta release (most stuff should be functioning and becoming stable)           January 11, 2018
# 4. Near-prime (release candidate)                                                To be determined
# 5. Prime release                                                                 January 21, 2018
# 6. 1.0-prime kits EOL                                                            February 1, 2018
#
# 1.3 development starts                                                           April 1, 2018
# 1.3 release                                                                      July 1, 2018
# 1.2-prime kits EOL                                                               August 1, 2018
#
#							NEW VERSION             EXISTING
#                           =======================================================
# core-kit                  1.2-prime
# security-kit              1.2-prime
# xorg-kit                                          1.19-prime
# gnome-kit                 3.26-prime              3.20-prime (also supported)
# kde-kit                                           5.10-prime
# media-kit                 1.2-prime
# perl-kit                                          5.26-prime
# > perl-modules-kit        1.2-prime
# python-kit                3.6-prime
# > python-modules-kit      1.2-prime
# php-kit                                           master
# java-kit                  1.2-prime
# ruby-kit                  1.2-prime
# haskell-kit               1.2-prime
# ml-lang-kit               1.2-prime
# lisp-scheme-kit           1.2-prime
# lang-kit                  1.2-prime
# llvm-kit                  1.2-prime
# dev-kit                   1.2-prime
# xfce-kit                                          4.12-prime
# desktop-kit               1.2-prime
# editors-kit                                       master
# net-kit                   1.2-prime
# text-kit                                          master
# science-kit                                       master
# games-kit                                         master
# nokit                                             master


# It has already been explained how when we apply package-set rules, we process the kit_source repositories in order and
# after we find a catpkg that matches, any matches in successive repositories for catpkgs that we have already copied
# over to the destination kit are *ignored*. This is implemented using a dictionary called "kitted_catpkgs".  Once a
# catpkg is inserted into a kit, it's no longer 'available' to be inserted into successive kits, to avoid duplicates.

class KitFoundation:

	kit_groups = {
		'prime': [
			{'name': 'core-kit', 'branch': '1.0-prime', 'source': 'gentoo_prime_protected', 'default': True},
			{'name': 'core-kit', 'branch': '1.1-prime', 'source': 'gentoo_prime_mk3_protected', 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'core-kit', 'branch': '1.2-prime', 'source': 'gentoo_prime_mk4_protected', 'stability': KitStabilityRating.PRIME},
			{'name': 'core-hw-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'security-kit', 'branch': '1.0-prime', 'source': 'gentoo_prime_protected', 'default': True},
			{'name': 'security-kit', 'branch': '1.1-prime', 'source': 'gentoo_prime_mk3_protected', 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'security-kit', 'branch': '1.2-prime', 'source': 'funtoo_current', 'stability': KitStabilityRating.PRIME},
			{'name': 'xorg-kit', 'branch': '1.17-prime', 'source': 'funtoo_prime_xorg', 'default': False, 'stability': KitStabilityRating.PRIME},
			{'name': 'xorg-kit', 'branch': '1.19-prime', 'source': 'funtoo_mk2_prime', 'default': True, 'stability': KitStabilityRating.PRIME},  # MK2
			{'name': 'xorg-kit', 'branch': '1.20-release', 'source': 'funtoo_current', 'default': False, 'stability': KitStabilityRating.DEV},
			{'name': 'gnome-kit', 'branch': '3.20-prime', 'source': 'funtoo_prime_gnome', 'default': False, 'stability' : KitStabilityRating.PRIME},
			{'name': 'gnome-kit', 'branch': '3.26-prime', 'source': 'funtoo_mk4_prime', 'default': True, 'stability': KitStabilityRating.PRIME},
			{'name': 'kde-kit', 'branch': '5.10-prime', 'source': 'funtoo_mk3_prime', 'default': False, 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'kde-kit', 'branch': '5.11-prime', 'source': 'funtoo_prime_kde', 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'kde-kit', 'branch': '5.12-prime', 'source': 'funtoo_prime_kde_late', 'default': True, 'stability': KitStabilityRating.PRIME},
			{'name': 'kde-kit', 'branch': '5.13-release', 'source': 'funtoo_current', 'default': False, 'stability': KitStabilityRating.DEV},
			{'name': 'media-kit', 'branch': '1.0-prime', 'source': 'funtoo_prime_media', 'default': False, 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'media-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_prime', 'default': True, 'stability': KitStabilityRating.PRIME},  # MK3
			{'name': 'media-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'perl-kit', 'branch': '5.24-prime', 'source': 'funtoo_prime_perl', 'default': True},
			{'name': 'perl-kit', 'branch': '5.26-prime', 'source': 'funtoo_mk3_prime', 'default': False, 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'perl-kit', 'branch': '5.28-release', 'source': 'funtoo_current', 'default': False, 'stability': KitStabilityRating.DEV},
			{'name': 'python-modules-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'python-kit', 'branch': '3.4-prime', 'source': 'funtoo_prime', 'default': True},
			{'name': 'python-kit', 'branch': '3.6-prime', 'source': 'funtoo_mk2_prime', 'default': False, 'stability': KitStabilityRating.PRIME},  # MK2
			{'name': 'python-kit', 'branch': '3.6.3-prime', 'source': 'funtoo_mk3_prime', 'default': False, 'stability': KitStabilityRating.DEPRECATED},  # MK3
			{'name': 'python-kit', 'branch': '3.7-release', 'source': 'funtoo_current', 'default': False, 'stability': KitStabilityRating.DEV},
			{'name': 'php-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			# We will freeze when 7.2.0 is released...
			{'name': 'java-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'java-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'ruby-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'ruby-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'haskell-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'haskell-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'ml-lang-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': False, 'stability': KitStabilityRating.DEPRECATED},
			{'name': 'ml-lang-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'default': True, 'stability': KitStabilityRating.PRIME},
			{'name': 'lisp-scheme-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'lisp-scheme-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'lang-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'lang-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'llvm-kit', 'branch': '1.2-prime', 'source': 'funtoo_prime_llvm', 'default': True, 'stability': KitStabilityRating.PRIME},
			{'name': 'llvm-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': False, 'stability': KitStabilityRating.DEV},
			{'name': 'dev-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'dev-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'xfce-kit', 'branch': '4.12-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'desktop-kit', 'branch': '1.1-prime', 'source': 'funtoo_mk3_late_prime', 'default': True},
			{'name': 'desktop-kit', 'branch': '1.2-prime', 'source': 'funtoo_mk4_prime', 'stability': KitStabilityRating.PRIME},
			{'name': 'editors-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'net-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'text-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'science-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'games-kit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT},
			{'name': 'nokit', 'branch': 'master', 'source': 'funtoo_current', 'default': True, 'stability': KitStabilityRating.CURRENT}
		]
	}

	python_kit_settings = {
		#	branch / primary python / alternate python / python mask (if any)
		'master': {
			"primary": "python3_6",
			"alternate": "python2_7",
			"mask": None
		},
		'3.4-prime': {
			"primary": "python3_4",
			"alternate": "python2_7",
			"mask": ">=dev-lang/python-3.5"
		},
		'3.6-prime': {
			"primary": "python3_6",
			"alternate": "python2_7",
			"mask": ">=dev-lang/python-3.7"
		},
		'3.6.3-prime': {
			"primary": "python3_6",
			"alternate": "python2_7",
			"mask": ">=dev-lang/python-3.7"
		}
	}

	release_info = {
		# set default release, currently not set. Can be used to set default kits.
		"default" : None
	}

	release_defs = {
		"1.2": {
			# first list entry is the default; second list entry is still considered to be "part of release"
			"core-kit": [ "1.2-prime" ],
			"python-kit": [ "3.6-prime" ],
			"security-kit": [ "1.2-prime"],
			"kde-kit": [ "5.12-prime" ],
			"media-kit": [ "1.2-prime" ],
			"java-kit": [ "1.2-prime" ],
			"ruby-kit": [ "1.2-prime" ],
			"haskell-kit": [ "1.2-prime" ],
			"lisp-scheme-kit": [ "1.2-prime" ],
			"lang-kit": [ "1.2-prime" ],
			"dev-kit": [ "1.2-prime" ],
			"desktop-kit": [ "1.2-prime" ],
			"gnome-kit": [ "3.26-prime", "3.20-prime" ]
		}
		# TODO: forgot to add perl-kit!!!
	}

	# KIT SOURCES - kit sources are a combination of overlays, arranged in a python list [ ]. A KIT SOURCE serves as a
	# unified collection of source catpkgs for a particular kit. Each kit can have one KIT SOURCE. KIT SOURCEs MAY be
	# shared among kits to avoid duplication and to help organization. Note that this is where we specify branch or SHA1
	# for each overlay.

	# Each kit source can be used as a source of catpkgs for a kit. Order is important -- package-set rules are applied in
	# the same order that the overlay appears in the kit_source_defs list -- so for "funtoo_current", package-set rules will
	# be applied to gentoo-staging first, then flora, then faustoo, then fusion809. Once a particular catpkg matches and is
	# copied into a dest-kit, a matching capkg in a later overlay, if one exists, will be ignored.

	# It is important to note that we support two kinds of kit sources -- the first is the gentoo-staging master repository
	# which contains a master set of eclasses and contains everything it needs for all the catpkgs it contains. The second
	# kind of repository we support is an overlay that is designed to be used with the gentoo-staging overlay, so it may
	# need some catpkgs (as dependencies) or eclasses from gentoo-staging. The gentoo-staging repository should always
	# appear as the first item in kit_source_defs, with the overlays appearing after.

	kit_source_defs = {
		"funtoo_current": [
			{"repo": "flora"},
			{"repo": "faustoo"},
			{"repo": "fusion809"},
			{"repo": "gentoo-staging"}
		],
		"funtoo_mk2_prime": [
			{"repo": "flora", },
			{"repo": "faustoo"},
			{"repo": "fusion809", "src_sha1": "489b46557d306e93e6dc58c11e7c1da52abd34b0", 'date': '31 Aug 2017'},
			{"repo": "gentoo-staging", "src_sha1": '80d2f3782e7f351855664919d679e94a95793a06', 'date': '31 Aug 2017'},
			# add current gentoo-staging to catch any new ebuilds that are not yet in our snapshot above (dev-foo/* match)
			{"repo": "gentoo-staging-underlay"},
		],
		"funtoo_mk3_prime": [
			{"repo": "flora", },
			{"repo": "faustoo", },
			{"repo": "fusion809", "src_sha1": "8733034816d3932486cb593db2dfbfbc7577e28b", 'date': '09 Oct 2017'},
			{"repo": "gentoo-staging", "src_sha1": '2de4b388863ab0dbbd291422aa556c9de646f1ff', 'date': '10 Oct 2017'},
			{"repo": "gentoo-staging-underlay"},
		],
		"funtoo_mk3_late_prime": [
			{"repo": "flora", },
			{"repo": "faustoo", },
			{"repo": "fusion809", "src_sha1": "574f9f6f69b30f4eec7aa2eb53f55059d3c05b6a", 'date': '23 Oct 2017'},
			{"repo": "gentoo-staging", "src_sha1": 'aa03020139bc129af2ad5f454640c102afa712e6', 'date': '22 Oct 2017'},
			{"repo": "gentoo-staging-underlay"},
		],

		"funtoo_mk4_prime": [
			{"repo": "flora", },
			{"repo": "faustoo", },
			{"repo": "fusion809", "src_sha1": "574f9f6f69b30f4eec7aa2eb53f55059d3c05b6a", 'date': '23 Oct 2017'},
			{"repo": "gentoo-staging", "src_sha1": 'bb740efd8e9667dc19f162e936c5c876fb716b5c', 'date': '19 Jan 2018'},
			{"repo": "gentoo-staging-underlay"},
		],

		"funtoo_prime": [
			{"repo": "flora", },
			{"repo": "faustoo", },
			{"repo": "fusion809", "src_sha1": "8322bcd79d47ef81f7417c324a1a2b4772020985"},
			{"repo": "gentoo-staging", "src_sha1": '06a1fd99a3ce1dd33724e11ae9f81c5d0364985e', 'date': '21 Apr 2017'},
			{"repo": "gentoo-staging-underlay"},
		],
		"gentoo_prime_mk3_protected": [
			# lock down core-kit and security-kit
			{"repo": "gentoo-staging", "src_sha1": '2de4b388863ab0dbbd291422aa556c9de646f1ff', 'date': '10 Oct 2017'},
		],
		"gentoo_prime_mk4_protected": [
			# lock down core-kit and security-kit
			{"repo": "gentoo-staging", "src_sha1": '887b32c487432a9206208fc42a313e9e0517bf2b', 'date': '8 Jan 2018'},
		],
		"gentoo_prime_protected": [
			# lock down core-kit and security-kit
			{"repo": "gentoo-staging", "src_sha1": '06a1fd99a3ce1dd33724e11ae9f81c5d0364985e', 'date': '21 Apr 2017'},
		],
		"gentoo_current_protected": [
			# lock down core-kit and security-kit
			{"repo": "gentoo-staging"},
		],
		"funtoo_prime_xorg": [
			# specific snapshot for xorg-kit
			{"repo": "gentoo-staging", 'src_sha1': 'a56abf6b7026dae27f9ca30ed4c564a16ca82685', 'date': '18 Nov 2016'}
		],
		"funtoo_prime_gnome": [
			# specific snapshot for gnome-kit
			{"repo": "gentoo-staging", 'src_sha1': '44677858bd088805aa59fd56610ea4fb703a2fcd', 'date': '18 Sep 2016'}
		],
		"funtoo_prime_media": [
			# specific snapshot for media-kit, though we should bump and expand this soon
			{"repo": "gentoo-staging", 'src_sha1': '355a7986f9f7c86d1617de98d6bf11906729f108', 'date': '25 Feb 2017'}
		],
		"funtoo_prime_perl": [
			# specific snapshot for perl-kit
			{"repo": "gentoo-staging", 'src_sha1': 'fc74d3206fa20caa19b7703aa051ff6de95d5588', 'date': '11 Jan 2017'}
		],
		"funtoo_prime_kde": [
			# specific snapshot for kde-kit
			{"repo": "gentoo-staging", 'src_sha1': '1a0337dbb94be980733eeb9d9661da58cffd4e59', 'date': '28 Jan 2018'}
		],
		"funtoo_prime_kde_late": [
			# specific snapshot for kde-kit
			{"repo": "gentoo-staging", 'src_sha1': '4d219563cd80de1a9a0ebb7c2718d8639415cc07', 'date': '10 Mar 2018'}
		],
		"funtoo_prime_llvm": [
			# specific snapshot for llvm-kit
			{"repo": "gentoo-staging", 'src_sha1': 'e4d303da8b2ad31692eddba258ef28b69fec3efb', 'date': '20 Mar 2018'}
		]
	}

	# OVERLAYS - lists sources for catpkgs, along with properties which can include "select" - a list of catpkgs to
	# include.  When "select" is specified, only these catpkgs will be available for selection by the package-set rules. .
	# If no "select" is specified, then by default all available catpkgs could be included, if they match patterns, etc. in
	# package-sets. Note that we do not specify branch or SHA1 here. This may vary based on kit, so it's specified elsewhere
	# (see KIT SOURCES, below.)

	@property
	def overlays(self):
		return {
			# use gentoo-staging-2017 dirname to avoid conflicts with ports-2012 generation
			"gentoo-staging": {"url": self.config.gentoo_staging, "dirname": "gentoo-staging-2017"},
			"gentoo-staging-underlay": {"url": self.config.gentoo_staging, "dirname": "gentoo-staging-2017-underlay"},
			"faustoo": {"url": "https://github.com/fmoro/faustoo.git", "eclasses": [
				"waf",
				"googlecode"
			],
			            # SKIP any catpkgs that also exist in gentoo-staging (like nvidia-drivers). All others will be copied.
			            "filter": ["gentoo-staging"],
			            # well, I lied. There are some catpkgs that exist in gentoo-staging that we DO want to copy. These are the
			            # ones we will copy. We need to specify each one. This list may change over time as faustoo/gentoo gets stale.
			            "force": [
				            "dev-java/maven-bin",
				            "dev-java/sun-java3d-bin",
				            "dev-php/pecl-mongo",
				            "dev-php/pecl-mongodb",
				            "dev-python/mongoengine",
				            "dev-python/pymongo",
				            "dev-util/idea-community",
				            "dev-util/webstorm",
				            "x11-wm/blackbox"
			            ]
			            },
			"fusion809": {"url": "https://github.com/fusion809/fusion809-overlay.git", "select": [
				"app-editors/atom-bin",
				"app-editors/notepadqq",
				"app-editors/bluefish",
				"app-editors/textadept",
				"app-editors/scite",
				"app-editors/gvim",
				"app-editors/vim",
				"app-editors/vim-core",
				"app-editors/sublime-text"
			]
			              },  # FL-3633, FL-3663, FL-3776
			"plex": {"url": "https://github.com/Ghent/funtoo-plex.git", "select": [
				"media-tv/plex-media-server",
			],
			         },
			# damex's deadbeef (music player like foobar2000) overlay
			"deadbeef": {"url": "https://github.com/damex/deadbeef-overlay.git", "copyfiles": {
				"profiles/package.mask": "profiles/package.mask/deadbeef.mask"
			},
			             },
			# damex's wmfs (window manager from scratch) overlay
			"wmfs": {"url": "https://github.com/damex/wmfs-overlay.git", "copyfiles": {
				"profiles/package.mask": "profiles/package.mask/wmfs.mask"
			},
			         },
			"flora": {"url": self.config.flora, "copyfiles": {
				"licenses/renoise-EULA": "licenses/renoise-EULA"
			},
			          },
		}

	def __init__(self, config):
		self.config = config
