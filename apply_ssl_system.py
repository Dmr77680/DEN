#!/usr/bin/env python3
"""DEN: implemente reellement ssl:s (Splatoon 3 / NPLN) comme Citron. Lancer a la racine du depot."""
import sys
p = 'src/core/hle/service/ssl/ssl.cpp'
s = open(p, encoding='utf-8').read()
if 'DEN_SSL_SYSTEM_APPLIED' in s:
    sys.exit('deja applique')
a = s.find('class ISslServiceForSystem final')
b = s.find('void LoopProcess(Core::System& system)')
if a < 0 or b < 0 or b < a:
    sys.exit('ancres introuvables')

NEW = r'''// DEN_SSL_SYSTEM_APPLIED
// [Nextendo] ssl:s partage les commandes 0-9 avec ssl. Ici elles n'etaient que des stubs
// vides (CreateContext ne renvoyait aucune interface, GetCertificates rien) : Splatoon 3
// (pile gRPC / NPLN) ouvre son contexte SSL via ssl:s et restait donc bloque juste apres
// la resolution DNS du serveur, sans jamais ouvrir de connexion. Port de l'implementation Citron.
class ISslServiceForSystem final : public ServiceFramework<ISslServiceForSystem> {
public:
    explicit ISslServiceForSystem(Core::System& system_)
        : ServiceFramework{system_, "ssl:s"}, cert_store{system} {
        // clang-format off
        static const FunctionInfo functions[] = {
            {0, &ISslServiceForSystem::CreateContext, "CreateContext"},
            {1, &ISslServiceForSystem::GetContextCount, "GetContextCount"},
            {2, D<&ISslServiceForSystem::GetCertificates>, "GetCertificates"},
            {3, D<&ISslServiceForSystem::GetCertificateBufSize>, "GetCertificateBufSize"},
            {4, nullptr, "DebugIoctl"},
            {5, &ISslServiceForSystem::SetInterfaceVersion, "SetInterfaceVersion"},
            {6, &ISslServiceForSystem::FlushSessionCache, "FlushSessionCache"},
            {7, &ISslServiceForSystem::StubSuccess, "SetDebugOption"},
            {8, &ISslServiceForSystem::GetDebugOption, "GetDebugOption"},
            {9, &ISslServiceForSystem::StubSuccess, "ClearTls12FallbackFlag"},
            {100, &ISslServiceForSystem::CreateContext, "CreateContextForSystem"},
            {101, &ISslServiceForSystem::StubSuccess, "SetThreadCoreMask"},
            {102, &ISslServiceForSystem::GetThreadCoreMask, "GetThreadCoreMask"},
            {103, &ISslServiceForSystem::StubSuccess, "VerifySignature"},
        };
        // clang-format on

        RegisterHandlers(functions);
    }

private:
    void CreateContext(HLERequestContext& ctx) {
        struct Parameters {
            SslVersion ssl_version;
            INSERT_PADDING_BYTES(0x4);
            u64 pid_placeholder;
        };
        static_assert(sizeof(Parameters) == 0x10, "Parameters is an invalid size");

        IPC::RequestParser rp{ctx};
        const auto parameters = rp.PopRaw<Parameters>();

        LOG_INFO(Service_SSL, "[Nextendo] ssl:s CreateContext, api_version={}",
                 parameters.ssl_version.api_version);

        IPC::ResponseBuilder rb{ctx, 2, 0, 1};
        rb.Push(ResultSuccess);
        rb.PushIpcInterface<ISslContext>(ctx, system, parameters.ssl_version);
    }

    void GetContextCount(HLERequestContext& ctx) {
        IPC::ResponseBuilder rb{ctx, 3};
        rb.Push(ResultSuccess);
        rb.Push<u32>(0);
    }

    Result GetCertificateBufSize(
        Out<u32> out_size, InArray<CaCertificateId, BufferAttr_HipcMapAlias> certificate_ids) {
        u32 num_entries;
        Result res = cert_store.GetCertificateBufSize(out_size, &num_entries, certificate_ids);
        LOG_INFO(Service_SSL, "[Nextendo] ssl:s GetCertificateBufSize -> size={} entries={}",
                 *out_size, num_entries);
        R_RETURN(res);
    }

    Result GetCertificates(Out<u32> out_num_entries, OutBuffer<BufferAttr_HipcMapAlias> out_buffer,
                           InArray<CaCertificateId, BufferAttr_HipcMapAlias> certificate_ids) {
        Result res = cert_store.GetCertificates(out_num_entries, out_buffer, certificate_ids);
        LOG_INFO(Service_SSL, "[Nextendo] ssl:s GetCertificates -> entries={}", *out_num_entries);
        R_RETURN(res);
    }

    void SetInterfaceVersion(HLERequestContext& ctx) {
        IPC::RequestParser rp{ctx};
        const u32 ssl_version = rp.Pop<u32>();
        LOG_DEBUG(Service_SSL, "called, ssl_version={}", ssl_version);

        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(ResultSuccess);
    }

    void FlushSessionCache(HLERequestContext& ctx) {
        IPC::ResponseBuilder rb{ctx, 3};
        rb.Push(ResultSuccess);
        rb.Push<u32>(0);
    }

    void GetDebugOption(HLERequestContext& ctx) {
        std::array<u8, 1> debug_value{0};
        ctx.WriteBuffer(debug_value);

        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(ResultSuccess);
    }

    void GetThreadCoreMask(HLERequestContext& ctx) {
        IPC::ResponseBuilder rb{ctx, 4};
        rb.Push(ResultSuccess);
        rb.Push<u64>(0);
        rb.Push<u32>(0);
    }

    void StubSuccess(HLERequestContext& ctx) {
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(ResultSuccess);
    }

    CertStore cert_store;
};

'''
s = s[:a] + NEW + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print('OK')
