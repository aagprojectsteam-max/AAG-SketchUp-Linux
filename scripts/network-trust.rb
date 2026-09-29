# SPDX-License-Identifier: MIT
# Prefix-local host CA integration for SketchUp's embedded Ruby/OpenSSL.
# SketchUp sets SSL_CERT_FILE to its bundled store during Ruby initialization.
# The launcher supplies an independently named, validated host bundle instead.
require 'digest'
module AAGHostTrust
  source = ENV['AAG_HOST_CA_BUNDLE']
  if source && !source.empty?
    raise 'Unexpected host CA path' unless source.start_with?('/')
    file = 'Z:' + source
    expected = ENV['AAG_HOST_CA_SHA256']
    raise 'Host CA bundle changed after launch' unless expected && Digest::SHA256.file(file).hexdigest == expected
    require 'openssl'
    # Preserve VERIFY_PEER, hostname checking and the existing store flags.
    # Refresh the already-created default store as well as future stores.
    ENV['SSL_CERT_FILE'] = file
    OpenSSL::SSL::SSLContext::DEFAULT_CERT_STORE.add_file(file)
    APPLIED = true
  end
end
