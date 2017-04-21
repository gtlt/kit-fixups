# Distributed under the terms of the GNU General Public License v2

EAPI=5
inherit autotools eutils toolchain-funcs

DESCRIPTION="lanmap sits quietly on a network and builds a picture of what it sees"
HOMEPAGE="http://www.parseerror.com/lanmap"
SRC_URI="http://www.parseerror.com/${PN}/rev/${PN}-2006-03-07-rev${PV}.zip"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="*"

CDEPEND="net-libs/libpcap"
RDEPEND="
	${CDEPEND}
	<=media-gfx/graphviz-2.28.0
"
DEPEND="
	${CDEPEND}
	app-arch/unzip
"

S=${WORKDIR}/${PN}

src_prepare() {
	epatch "${FILESDIR}"/${P}-make.patch
	rm configure || die
	eautoreconf
}

src_compile() {
	emake CC="$(tc-getCC)"
}

src_install() {
	emake prefix="${ED}"/usr install
	dodoc README.txt TODO.txt
}