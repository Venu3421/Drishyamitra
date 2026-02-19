import os
# Ensure env var is set if not already (though we set it in .env, checking effective env)
if "TF_ENABLE_ONEDNN_OPTS" not in os.environ:
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf

# Configure logger first
tf.get_logger().setLevel("ERROR")

print(f"TensorFlow version: {tf.__version__}")

try:
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(10, activation="softmax")
    ])
    print("Setup OK")
except Exception as e:
    print(f"Setup FAILED: {e}")
