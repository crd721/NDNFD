VERSION='0.1'
APPNAME='NDNFD'

import waflib


def options(opt):
    opt.load('compiler_c compiler_cxx')
    opt.load('ccnx', tooldir='.')

    opt.add_option('--optimize',action='store_true',default=False,dest='optimize',help='optimize object code')
    opt.add_option('--gtest',action='store_true',default=False,dest='gtest',help='build unit tests')
    opt.add_option('--markdown',action='store_true',default=False,dest='markdown',help='build Markdown into HTML')
    opt.add_option('--sim',action='store_true',default=False,dest='sim',help='build library for ns-3 simulation')


def configure(conf):
    gcclibpath = None
    use_clang = False
    if waflib.Utils.unversioned_sys_platform() == 'freebsd':
        if not conf.env.CC:
            try:
                conf.find_program('gcc48', var='CC')
            except:
                try:
                    conf.find_program('gcc47', var='CC')
                except: pass
        if not conf.env.CXX:
            try:
                conf.find_program('g++48', var='CXX')
                gcclibpath = '/usr/local/lib/gcc48'
            except:
                try:
                    conf.find_program('g++47', var='CXX')
                    gcclibpath = '/usr/local/lib/gcc47'
                except: pass
    if waflib.Utils.unversioned_sys_platform() == 'darwin':
        if not conf.env.CC:
            try:
                conf.find_program('clang', var='CC')
                use_clang = True
            except: pass
        if not conf.env.CXX:
            try:
                conf.find_program('clang++', var='CXX')
                use_clang = True
            except: pass
    
    conf.load('compiler_c compiler_cxx')
    conf.load('ccnx', tooldir='.')
    
    conf.check_ccnx(path=conf.options.ccnx_dir)
    conf.check_cc(lib='pcap', header_name='pcap.h', define_name='HAVE_PCAP', uselib_store='PCAP')
    
    libresolv = 'resolv'
    if waflib.Utils.unversioned_sys_platform() == 'freebsd':
        libresolv = [] #FreeBSD has resolver in libc
    conf.check_cc(msg='Checking for resolv', lib=libresolv, fragment='#include <netinet/in.h>\n#include <arpa/nameser.h>\n#include <resolv.h>\nint main() { return 0; }', define_name='HAVE_RESOLV', uselib_store='RESOLV')

    conf.define('_GNU_SOURCE', 1)
    flags = ['-Wall', '-Werror', '-Wpointer-arith', '-fPIC']
    cxxflags_strict = ['-fno-rtti']
    if conf.options.sim:
        conf.env.SIM = 1
        cxxflags_strict = []
    conf.env.append_unique('CFLAGS', flags + ['-Wstrict-prototypes', '-std=c99'])
    conf.env.append_unique('CXXFLAGS', flags + ['-fno-exceptions', '-std=c++0x'] + cxxflags_strict)
    if use_clang:
        conf.env.append_unique('CXXFLAGS', ['-stdlib=libc++'])
        conf.env.append_unique('LINKFLAGS', ['-stdlib=libc++'])
    if not use_clang:
        conf.env.append_unique('LIBPATH', ['/usr/lib/i386-linux-gnu', '/usr/lib/x86_64-linux-gnu'])
        if gcclibpath is not None:
            conf.env.append_unique('LIBPATH', [gcclibpath])

    if conf.options.optimize:
        conf.env.append_unique('CFLAGS', ['-O3', '-g1'])
        conf.env.append_unique('CXXFLAGS', ['-O3', '-g1'])
    else:
        conf.env.append_unique('CFLAGS', ['-O0', '-g3'])
        conf.env.append_unique('CXXFLAGS', ['-O0', '-g3'])

    if conf.options.gtest:
        conf.env.GTEST = 1
        if waflib.Utils.unversioned_sys_platform() == 'linux' and not conf.env.LIB_PTHREAD:
            conf.check_cxx(lib='pthread')
        if use_clang:
            conf.env.append_unique('CXXFLAGS', ['-DGTEST_HAS_TR1_TUPLE=0','-DGTEST_HAS_RTTI=0'])
    
    if conf.options.markdown:
        conf.env.MARKDOWN = 1
        conf.find_program('pandoc', var='PANDOC')

    if gcclibpath is not None:
        # static link libstdc++ if non-default version is used, so that no LD_LIBRARY_PATH is required
        conf.env.append_unique('LINKFLAGS', ['-static-libstdc++'])


def build(bld):
    source_subdirs = ['core','util','face','message','strategy']
    bld.objects(target='ndnfdcommon',
        source=bld.path.ant_glob([subdir+'/*.cc' for subdir in source_subdirs], excl=['**/*_test*.cc']),
        includes='.',
        export_includes='.',
        use='CCNX PCAP ccnd/ccndcore ndnld/ndnldcore',
        )
        
    bld.objects(target='ccnd/ccndcore',
        source=['ccnd/ccnd.c','ccnd/ccnd_internal_client.c','ccnd/ccnd_stats.c','ccnd/ccnd_msg.c'],
        includes='.',
        use='CCNX pthread',
        )

    bld.objects(target='ndnld/ndnldcore',
        source=bld.path.ant_glob(['ndnld/*.c']),
        use='CCNX',
        )
    
    bld.program(target='ndnfd',
        source=['command/ndnfd.cc'],
        includes='.',
        use='ccnd/ccndcore ndnld/ndnldcore ndnfdcommon',
        )
    
    if bld.env.SIM:
        bld.stlib(target='ndnfdsim',
            source=['command/ndnfdsim.cc'],
            use='ccnd/ccndcore ndnld/ndnldcore ndnfdcommon',
            )
    
    bld.program(target='ndnfdc',
        source=bld.path.ant_glob(['command/ndnfdc/*.c']),
        includes='.',
        use='CCNX RESOLV',
        )

    if bld.env.GTEST:
        try:
            bld.get_tgen_by_name('pthread')
        except:
            bld.read_shlib('pthread', paths=bld.env.LIBPATH)
        bld.stlib(target='gtest/gtest',
            source=['gtest/gtest.cc', 'gtest/gtest_main.cc'],
            includes='. gtest',
            use='pthread',
            )
        bld.program(target='unittest',
            source=bld.path.ant_glob([subdir+'/*_test*.cc' for subdir in source_subdirs]),
            use='common ndnfdcommon gtest/gtest',
            install_path=None,
            )
    
    if bld.env.MARKDOWN:
        waflib.TaskGen.declare_chain(name='markdown2html',
            rule='${PANDOC} -f markdown -t html -o ${TGT} ${SRC}',
            shell=False,
            ext_in='.md',
            ext_out='.htm',
            reentrant=False,
            install_path=None,
            )
        bld(source=bld.path.ant_glob(['**/*.md']))


def check(ctx):
    unittest_node=ctx.root.find_node(waflib.Context.out_dir+'/unittest')
    if unittest_node is None:
        ctx.fatal('unittest is not built; configure with --gtest and build')
    else:
        import subprocess
        subprocess.call(unittest_node.abspath())

