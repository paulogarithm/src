define luau
	git clone https://github.com/roblox/luau
	[CD] luau
	make
	[LINK] luau -> luau
	[LINK] luau-compile -> luau-compile
	[LINK] luau-analyze -> luau-analyze
endef

define watchexec
	[INSTALL] cargo rustc
	git clone https://github.com/watchexec/watchexec.git
	[CD] watchexec
	cargo clean
	cargo build --release
	[LINK] watchexec -> target/release/watchexec
endef

# define criterion
# 	git clone https://github.com/Snaipe/Criterion
# 	ifndef meson
# 		wget https://github.com/mesonbuild/meson/releases/download/1.2.1/meson-1.2.1.tar.gz
# 		tar -xvzf meson*.tar.gz
# 		[CD] meson*/
# 		[LINK] meson -> meson.py
# 		[CD] ..
# 	endif
# 	[CD] Criterion
# 	meson build
# 	[CD] build && ninja
# 	[CD] src
# 	sudo rm /usr/local/lib/libcriterion.so
# 	sudo cp $PWD/libcriterion.so.3.2.0 $PWD/libcriterion.so.3 $PWD/libcriterion.so /usr/local/lib/
# 	export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
# endef

define criterion
	git clone https://github.com/Snaipe/Criterion
	mv Criterion/ criterion/
	[CD] criterion/include
	sudo cp -r criterion /usr/local/include
endef

define test
	[INSTALL] tree
endef
