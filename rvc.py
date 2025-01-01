import replicate


def create_rvc_conversion(audio, model_url, t_id, pitch=0, voice_name=None):
    input = {
        "protect": 0.5,
        "rvc_model": "CUSTOM",  # to use custom = CUSTOM
        "index_rate": 0.5,
        "input_audio": audio,
        "pitch_change": pitch,
        "rms_mix_rate": 0.3,
        "filter_radius": 3,
        "custom_rvc_model_download_url": model_url,
        "output_format": "mp3",
    }

    callback_url = (
        f"https://n8n.inbeet.tech/webhook/replicate?t_id={t_id}&voice={voice_name}"
    )

    replicate.predictions.create(
        version="d18e2e0a6a6d3af183cc09622cebba8555ec9a9e66983261fc64c8b1572b7dce",
        input=input,
        webhook=callback_url,
        webhook_events_filter=["completed"],
    )
