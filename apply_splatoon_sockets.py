#!/usr/bin/env python3
"""DEN : sockets pour Splatoon 3 (IPv6 refuse proprement, eventfd reel, options socket tolerantes).
Lancer a la racine du depot."""
import sys

def rd(p):
    return open(p, encoding='utf-8').read()

def wr(p, s):
    open(p, 'w', encoding='utf-8', newline='\n').write(s)

def rep(s, old, new, what, count=1):
    if s.count(old) != count:
        sys.exit('ANCRE INTROUVABLE/AMBIGUE (%s): %d occurrence(s)' % (what, s.count(old)))
    return s.replace(old, new)

H = 'src/core/hle/service/sockets/bsd.h'
C = 'src/core/hle/service/sockets/bsd.cpp'
S = 'src/core/hle/service/sockets/sockets.h'

h = rd(H)
if 'DEN_SOCKETS_APPLIED' in h:
    sys.exit('deja applique')

# ---- sockets.h : errno AFNOSUPPORT
s = rd(S)
s = rep(s, '    PIPE = 32,\n', '    PIPE = 32,\n    AFNOSUPPORT = 97,\n', 'sockets.h errno')
wr(S, s)

# ---- bsd.h
h = rep(h, '#include <memory>\n#include <span>\n',
        '// DEN_SOCKETS_APPLIED\n#include <array>\n#include <map>\n#include <memory>\n#include <optional>\n#include <span>\n',
        'bsd.h includes')
h = rep(h, '        bool is_connection_based = false;\n    };\n',
        '        bool is_connection_based = false;\n'
        '        // [Nextendo] Cree par EventFd() : un socket UDP boucle sur lui-meme qui sert de\n'
        '        // "self-pipe" de reveil (gRPC de Splatoon 3 en depend).\n'
        '        bool is_eventfd = false;\n'
        '        // [Nextendo] Options socket "acceptees mais simulees" : le jeu les relit juste apres\n'
        '        // les avoir posees pour verifier qu\'elles ont pris, on lui renvoie donc la valeur posee.\n'
        '        std::map<std::pair<u32, u32>, std::vector<u8>> feigned_opts;\n'
        '    };\n', 'bsd.h FileDescriptor')
wr(H, h)

c = rd(C)

# ---- includes
c = rep(c, '#include <array>\n#include <atomic>\n#include <memory>\n#include <utility>\n#include <vector>\n',
        '#include <algorithm>\n#include <array>\n#include <atomic>\n#include <cstring>\n#include <memory>\n#include <tuple>\n#include <utility>\n#include <vector>\n',
        'bsd.cpp includes')

# ---- SocketImpl : refuser les familles autres qu'IPv4
c = rep(c, '    [[maybe_unused]] const bool unk_flag = (static_cast<u32>(type) & 0x20000000) != 0;\n',
        '    // [Nextendo] Splatoon 3 (gRPC/NPLN) tente d\'abord une socket IPv6 (domain=28) puis retombe\n'
        '    // sur IPv4 si elle echoue. Eden ne gere que IPv4 : il faut un echec propre (EAFNOSUPPORT)\n'
        '    // et non une socket a moitie creee, sinon le jeu plante ensuite.\n'
        '    if (domain != Domain::INET && domain != Domain::Unspecified) {\n'
        '        LOG_WARNING(Service, "[Nextendo] Socket domain={} non supporte (IPv6 ?), EAFNOSUPPORT",\n'
        '                    static_cast<u32>(domain));\n'
        '        return {-1, Errno::AFNOSUPPORT};\n'
        '    }\n\n'
        '    [[maybe_unused]] const bool unk_flag = (static_cast<u32>(type) & 0x20000000) != 0;\n',
        'SocketImpl domain')

# ---- BindImpl / ConnectImpl : adresse IPv6 (28 octets) refusee proprement
c = rep(c, '    ASSERT(addr.size() >= 16);\n    if (!file_descriptors[fd]->socket) {\n        LOG_WARNING(Service, "Uninitialized socket");\n        return Errno::BADF;\n    }\n\n    auto addr_in = GetValue<SockAddrIn>(addr);\n    const auto host_bind',
        '    if (!file_descriptors[fd]->socket) {\n        LOG_WARNING(Service, "Uninitialized socket");\n        return Errno::BADF;\n    }\n'
        '    // [Nextendo] sockaddr_in6 (28 octets) : IPv6 non supporte, echec propre pour que le jeu retombe sur IPv4.\n'
        '    if (addr.size() != sizeof(SockAddrIn)) {\n'
        '        LOG_WARNING(Service, "[Nextendo] Bind fd={} adresse de taille {} (IPv6 ?), EAFNOSUPPORT", fd, addr.size());\n'
        '        return Errno::AFNOSUPPORT;\n'
        '    }\n\n'
        '    auto addr_in = GetValue<SockAddrIn>(addr);\n    const auto host_bind',
        'BindImpl')
c = rep(c, '    ASSERT(addr.size() >= 16);\n    if (!file_descriptors[fd]->socket) {\n        LOG_WARNING(Service, "Uninitialized socket");\n        return Errno::BADF;\n    }\n\n    auto addr_in = GetValue<SockAddrIn>(addr);\n\n    auto translated_addr',
        '    if (!file_descriptors[fd]->socket) {\n        LOG_WARNING(Service, "Uninitialized socket");\n        return Errno::BADF;\n    }\n'
        '    if (addr.size() != sizeof(SockAddrIn)) {\n'
        '        LOG_WARNING(Service, "[Nextendo] Connect fd={} adresse de taille {} (IPv6 ?), EAFNOSUPPORT", fd, addr.size());\n'
        '        return Errno::AFNOSUPPORT;\n'
        '    }\n\n'
        '    auto addr_in = GetValue<SockAddrIn>(addr);\n\n    auto translated_addr',
        'ConnectImpl')

# ---- Read : vrai Read (eventfd + sockets)
a = c.find('void BSD_USA::Read(HLERequestContext& ctx) {')
b = c.find('void BSD_USA::Close(HLERequestContext& ctx) {')
if a < 0 or b < a:
    sys.exit('ancres Read/Close introuvables')
NEW_READ = r'''void BSD_USA::Read(HLERequestContext& ctx) {
    IPC::RequestParser rp{ctx};
    const s32 fd = rp.Pop<s32>();

    LOG_DEBUG(Service, "called. fd={} len={}", fd, ctx.GetWriteBufferSize());

    // [Nextendo] Un vrai eventfd_read() vide un compteur cumule. Notre socket de secours met
    // chaque Write() dans un datagramme separe : on les vide et on les additionne ici.
    if (IsFileDescriptorValid(fd) && file_descriptors[fd]->is_eventfd) {
        u64 total = 0;
        s32 drained = 0;
        Errno last_errno = Errno::SUCCESS;
        for (int i = 0; i < 1024; ++i) {
            // Seule la premiere lecture peut bloquer ; les suivantes verifient juste s'il reste
            // quelque chose, sinon un recv() bloquant figerait ce thread.
            if (i > 0) {
                std::vector<Network::PollFD> peek_fds{Network::PollFD{
                    .socket = file_descriptors[fd]->socket.get(),
                    .events = Network::PollEvents::In,
                    .revents = Network::PollEvents{},
                }};
                const auto [peek_ret, peek_errno] = Network::Poll(peek_fds, 0);
                if (peek_ret <= 0 || peek_errno != Network::Errno::SUCCESS ||
                    False(peek_fds[0].revents & Network::PollEvents::In)) {
                    break;
                }
            }
            std::vector<u8> chunk(sizeof(u64));
            const auto [chunk_ret, chunk_errno] = RecvImpl(fd, 0, chunk);
            if (chunk_ret != static_cast<s32>(sizeof(u64))) {
                last_errno = chunk_errno;
                break;
            }
            u64 value;
            std::memcpy(&value, chunk.data(), sizeof(value));
            total += value;
            ++drained;
        }

        IPC::ResponseBuilder rb{ctx, 4};
        if (drained > 0) {
            std::vector<u8> message(sizeof(u64));
            std::memcpy(message.data(), &total, sizeof(total));
            ctx.WriteBuffer(message);
            rb.Push(ResultSuccess);
            rb.Push<s32>(static_cast<s32>(sizeof(u64)));
            rb.PushEnum(Errno::SUCCESS);
        } else {
            rb.Push(ResultSuccess);
            rb.Push<s32>(-1);
            rb.PushEnum(last_errno);
        }
        return;
    }

    if (!IsFileDescriptorValid(fd)) {
        IPC::ResponseBuilder rb{ctx, 4};
        rb.Push(ResultSuccess);
        rb.Push<s32>(-1);
        rb.PushEnum(Errno::BADF);
        return;
    }

    std::vector<u8> message(ctx.GetWriteBufferSize());
    const auto [ret, bsd_errno] = RecvImpl(fd, 0, message);
    ctx.WriteBuffer(message);

    IPC::ResponseBuilder rb{ctx, 4};
    rb.Push(ResultSuccess);
    rb.Push<s32>(ret);
    rb.PushEnum(bsd_errno);
}

'''
c = c[:a] + NEW_READ + c[b:]

# ---- EventFd
a = c.find('void BSD_USA::EventFd(HLERequestContext& ctx) {')
b = c.find('template <typename Work>\nvoid BSD_USA::ExecuteWork')
if a < 0 or b < a:
    sys.exit('ancres EventFd introuvables')
NEW_EVT = r'''void BSD_USA::EventFd(HLERequestContext& ctx) {
    IPC::RequestParser rp{ctx};
    const u64 initval = rp.Pop<u64>();
    const u32 flags = rp.Pop<u32>();

    LOG_DEBUG(Service, "called. initval={} flags={}", initval, flags);

    // [Nextendo] Vrai eventfd, construit avec un socket UDP connecte a lui-meme en loopback :
    // Write() ajoute un datagramme (lisible/poll-able), Read() le vide. Les jeux s'en servent
    // pour reveiller un Poll bloque depuis un autre thread (gRPC de Splatoon 3 notamment).
    // Avant, ce n'etait qu'un stub qui ne renvoyait aucun fd valide.
    const s32 fd = FindFreeFileDescriptorHandle();
    if (fd < 0) {
        LOG_ERROR(Service, "No more file descriptors available");
        IPC::ResponseBuilder rb{ctx, 4};
        rb.Push(ResultSuccess);
        rb.Push<s32>(-1);
        rb.PushEnum(Errno::MFILE);
        return;
    }

    auto socket = std::make_shared<Network::Socket>();
    Network::Errno net_err = socket->Initialize(Network::Domain::INET, Network::Type::DGRAM,
                                                Network::Protocol::UDP);
    const Network::SockAddrIn loopback{
        .family = Network::Domain::INET,
        .ip = {127, 0, 0, 1},
        .portno = 0,
    };
    if (net_err == Network::Errno::SUCCESS) {
        net_err = socket->Bind(loopback);
    }
    Network::SockAddrIn bound{};
    if (net_err == Network::Errno::SUCCESS) {
        std::tie(bound, net_err) = socket->GetSockName();
    }
    if (net_err == Network::Errno::SUCCESS) {
        bound.ip = loopback.ip;
        net_err = socket->Connect(bound);
    }
    if (net_err != Network::Errno::SUCCESS) {
        LOG_ERROR(Service, "Failed to create eventfd backing socket, errno={}",
                  static_cast<int>(net_err));
        IPC::ResponseBuilder rb{ctx, 4};
        rb.Push(ResultSuccess);
        rb.Push<s32>(-1);
        rb.PushEnum(Translate(net_err));
        return;
    }

    file_descriptors[fd] = FileDescriptor{};
    FileDescriptor& descriptor = *file_descriptors[fd];
    descriptor.socket = std::move(socket);
    descriptor.is_connection_based = true; // permet Write()/Send() sans adresse de destination
    descriptor.is_eventfd = true;

    if (initval > 0) {
        const u64 seed = initval;
        descriptor.socket->Send(
            std::span<const u8>{reinterpret_cast<const u8*>(&seed), sizeof(seed)}, 0);
    }

    LOG_INFO(Service, "[Nextendo] New eventfd fd={} initval={}", fd, initval);

    IPC::ResponseBuilder rb{ctx, 4};
    rb.Push(ResultSuccess);
    rb.Push<s32>(fd);
    rb.PushEnum(Errno::SUCCESS);
}

'''
c = c[:a] + NEW_EVT + c[b:]

# ---- Get/SetSockOptImpl
a = c.find('Errno BSD_USA::GetSockOptImpl(')
b = c.find('Errno BSD_USA::ShutdownImpl(')
if a < 0 or b < a:
    sys.exit('ancres sockopt introuvables')
NEW_OPT = r'''Errno BSD_USA::GetSockOptImpl(s32 fd, u32 level, OptName optname, std::vector<u8>& optval) {
    if (!IsFileDescriptorValid(fd)) {
        return Errno::BADF;
    }
    if (!file_descriptors[fd]->socket) {
        LOG_WARNING(Service, "Uninitialized socket");
        return Errno::BADF;
    }

    FileDescriptor& descriptor = *file_descriptors[fd];
    Network::SocketBase* const socket = descriptor.socket.get();

    // Seule vraie lecture cote hote : l'erreur en attente.
    if (level == static_cast<u32>(SocketLevel::SOCKET) && optname == OptName::ERROR_) {
        auto [pending_err, getsockopt_err] = socket->GetPendingError();
        if (getsockopt_err == Network::Errno::SUCCESS) {
            Errno translated_pending_err = Translate(pending_err);
            ASSERT_OR_EXECUTE_MSG(
                optval.size() == sizeof(Errno), { return Errno::INVAL; },
                "Incorrect getsockopt option size");
            optval.resize(sizeof(Errno));
            PutValue(optval, translated_pending_err);
        }
        return Translate(getsockopt_err);
    }

    // [Nextendo] Tout le reste : on renvoie la valeur que le jeu vient de poser (il la relit
    // pour verifier -- TCP_NODELAY, REUSEADDR, option privee 0x80000001 de Splatoon 3...), ou
    // des zeros si rien n'a ete pose. Echouer ici faisait abandonner une socket pourtant bonne.
    const auto key = std::make_pair(level, static_cast<u32>(optname));
    if (const auto it = descriptor.feigned_opts.find(key); it != descriptor.feigned_opts.end()) {
        const size_t n = (std::min)(optval.size(), it->second.size());
        std::fill(optval.begin(), optval.end(), u8{0});
        std::copy_n(it->second.begin(), n, optval.begin());
        return Errno::SUCCESS;
    }
    LOG_WARNING(Service, "(STUBBED) getsockopt level={} optname=0x{:x}, zeroed value", level,
                static_cast<u32>(optname));
    std::fill(optval.begin(), optval.end(), u8{0});
    return Errno::SUCCESS;
}

Errno BSD_USA::SetSockOptImpl(s32 fd, u32 level, OptName optname, std::span<const u8> optval) {
    if (!IsFileDescriptorValid(fd)) {
        return Errno::BADF;
    }
    if (!file_descriptors[fd]->socket) {
        LOG_WARNING(Service, "Uninitialized socket");
        return Errno::BADF;
    }

    FileDescriptor& descriptor = *file_descriptors[fd];
    Network::SocketBase* const socket = descriptor.socket.get();

    // On memorise toute option posee pour pouvoir la renvoyer a getsockopt.
    const auto key = std::make_pair(level, static_cast<u32>(optname));
    const auto remember = [&] {
        descriptor.feigned_opts[key] = std::vector<u8>(optval.begin(), optval.end());
    };

    // Autres niveaux que SOL_SOCKET (TCP_NODELAY, IPv6...) et option privee 0x80000001 de
    // Splatoon 3 (8 octets) : acceptes sans toucher a la vraie socket.
    if (level != static_cast<u32>(SocketLevel::SOCKET) ||
        static_cast<u32>(optname) == 0x80000001) {
        LOG_DEBUG(Service, "[Nextendo] setsockopt simule level={} optname=0x{:x} len={}", level,
                  static_cast<u32>(optname), optval.size());
        remember();
        return Errno::SUCCESS;
    }

    if (optname == OptName::LINGER) {
        if (optval.size() != sizeof(Linger)) {
            LOG_WARNING(Service, "LINGER optval size mismatch: expected {}, got {}",
                        sizeof(Linger), optval.size());
            return Errno::INVAL;
        }
        auto linger = GetValue<Linger>(optval);
        if (linger.onoff != 0 && linger.onoff != 1) {
            return Errno::INVAL;
        }
        remember();
        return Translate(socket->SetLinger(linger.onoff != 0, linger.linger));
    }

    if (optval.size() != sizeof(u32)) {
        // Option de forme inattendue : on l'accepte en la simulant plutot que d'echouer/planter.
        LOG_WARNING(Service, "(STUBBED) setsockopt optname=0x{:x} optlen={}, simule",
                    static_cast<u32>(optname), optval.size());
        remember();
        return Errno::SUCCESS;
    }
    auto value = GetValue<u32>(optval);

    switch (optname) {
    case OptName::REUSEADDR:
        remember();
        return Translate(socket->SetReuseAddr(value != 0));
    case OptName::KEEPALIVE:
        remember();
        return Translate(socket->SetKeepAlive(value != 0));
    case OptName::BROADCAST:
        remember();
        return Translate(socket->SetBroadcast(value != 0));
    case OptName::SNDBUF:
        remember();
        return Translate(socket->SetSndBuf(value));
    case OptName::RCVBUF:
        remember();
        return Translate(socket->SetRcvBuf(value));
    case OptName::SNDTIMEO:
        remember();
        return Translate(socket->SetSndTimeo(value));
    case OptName::RCVTIMEO:
        remember();
        return Translate(socket->SetRcvTimeo(value));
    case OptName::NOSIGPIPE:
        LOG_WARNING(Service, "(STUBBED) setting NOSIGPIPE to {}", value);
        remember();
        return Errno::SUCCESS;
    default:
        LOG_WARNING(Service, "(STUBBED) setsockopt optname=0x{:x}, simule",
                    static_cast<u32>(optname));
        remember();
        return Errno::SUCCESS;
    }
}

'''
c = c[:a] + NEW_OPT + c[b:]
wr(C, c)
print('OK')
