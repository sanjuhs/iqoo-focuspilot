#include "core.h"
#include <jni.h>
#include <memory>
#include <unordered_map>
#include <stdexcept>
#include <codecvt>
#include <locale>

static std::mutex registry_mutex;
static std::unordered_map<jlong,std::shared_ptr<LocalModel>> registry;
static jlong next_handle=1;
static void fail(JNIEnv * env,const std::exception & error) {env->ThrowNew(env->FindClass("java/lang/IllegalStateException"),error.what());}
static std::string utf8(JNIEnv * env,jstring value) {
    if(!value) throw std::runtime_error("String argument is null");
    // JNI's GetStringUTFChars uses modified UTF-8, which is incorrect for emoji/
    // supplementary characters. Convert UTF-16 to standard UTF-8 for llama tokenization.
    const jchar * characters=env->GetStringChars(value,nullptr);
    if(!characters) throw std::runtime_error("Could not read UTF-16 argument");
    const jsize length=env->GetStringLength(value);
    std::string result;
    bool valid=true;
    for(jsize i=0;i<length;++i) {
        uint32_t code=characters[i];
        if(code>=0xd800 && code<=0xdbff) {
            if(i+1>=length || characters[i+1]<0xdc00 || characters[i+1]>0xdfff) {valid=false;break;}
            code=0x10000+((code-0xd800)<<10)+(characters[++i]-0xdc00);
        } else if(code>=0xdc00 && code<=0xdfff) {valid=false;break;}
        if(code<0x80) result.push_back(static_cast<char>(code));
        else if(code<0x800) {result.push_back(0xc0|(code>>6));result.push_back(0x80|(code&0x3f));}
        else if(code<0x10000) {result.push_back(0xe0|(code>>12));result.push_back(0x80|((code>>6)&0x3f));result.push_back(0x80|(code&0x3f));}
        else {result.push_back(0xf0|(code>>18));result.push_back(0x80|((code>>12)&0x3f));result.push_back(0x80|((code>>6)&0x3f));result.push_back(0x80|(code&0x3f));}
    }
    env->ReleaseStringChars(value,characters);
    if(!valid) throw std::runtime_error("Invalid UTF-16 argument");
    return result;
}
static std::shared_ptr<LocalModel> lookup(jlong handle) {
    std::lock_guard<std::mutex> lock(registry_mutex);
    auto found=registry.find(handle);
    if(found==registry.end()) throw std::runtime_error("Local model handle is closed or invalid");
    return found->second;
}
extern "C" JNIEXPORT jlong JNICALL Java_dev_focuspilot_prototype_LocalModel_nativeInit(JNIEnv * env,jclass,jstring path,jint context,jint threads) {
    try { auto value=std::make_shared<LocalModel>(utf8(env,path),context,threads);
        std::lock_guard<std::mutex> lock(registry_mutex);const auto handle=next_handle++;registry.emplace(handle,value);return handle;
    }catch(const std::exception & error){fail(env,error);return 0;}
}
extern "C" JNIEXPORT void JNICALL Java_dev_focuspilot_prototype_LocalModel_nativePrepare(JNIEnv * env,jclass,jlong handle) {
    try {lookup(handle)->prepare();}catch(const std::exception & error){fail(env,error);}
}
extern "C" JNIEXPORT jstring JNICALL Java_dev_focuspilot_prototype_LocalModel_nativeGenerate(JNIEnv * env,jclass,jlong handle,jstring prompt,jstring grammar,jint maximum,jboolean capture) {
    try {const auto output=lookup(handle)->generate(utf8(env,prompt),utf8(env,grammar),maximum,capture);
        std::wstring_convert<std::codecvt_utf8_utf16<char16_t>,char16_t> converter;
        const auto utf16=converter.from_bytes(output);
        return env->NewString(reinterpret_cast<const jchar *>(utf16.data()),utf16.size());}catch(const std::exception & error){fail(env,error);return nullptr;}
}
extern "C" JNIEXPORT void JNICALL Java_dev_focuspilot_prototype_LocalModel_nativeCancel(JNIEnv * env,jclass,jlong handle) {
    (void)env;
    std::shared_ptr<LocalModel> value;
    {std::lock_guard<std::mutex> lock(registry_mutex);auto found=registry.find(handle);if(found==registry.end())return;value=found->second;}
    value->cancel();
}
extern "C" JNIEXPORT void JNICALL Java_dev_focuspilot_prototype_LocalModel_nativeClose(JNIEnv *,jclass,jlong handle) {
    std::shared_ptr<LocalModel> value;
    {std::lock_guard<std::mutex> lock(registry_mutex);auto found=registry.find(handle);if(found==registry.end())return;value=found->second;registry.erase(found);}
    value->shutdown(); // shared ownership lets in-flight calls finish; queued calls refuse to start.
}
