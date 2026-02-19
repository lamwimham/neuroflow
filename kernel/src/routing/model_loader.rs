//! Sentence-BERT模型加载器
//! 
//! 负责加载和管理Sentence-BERT模型，用于生成文本嵌入向量

use std::sync::{Arc, RwLock};
use std::path::Path;
use std::error::Error;
use serde::{Deserialize, Serialize};

/// 模型配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelConfig {
    pub model_path: String,
    pub cache_dir: Option<String>,
    pub batch_size: usize,
    pub max_sequence_length: usize,
    pub pooling_strategy: PoolingStrategy,
}

impl Default for ModelConfig {
    fn default() -> Self {
        Self {
            model_path: "sentence-transformers/all-MiniLM-L6-v2".to_string(),
            cache_dir: None,
            batch_size: 16,
            max_sequence_length: 512,
            pooling_strategy: PoolingStrategy::Mean,
        }
    }
}

/// 池化策略
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PoolingStrategy {
    Mean,
    Max,
    CLS,
    LastToken,
}

/// 文本编码器
pub struct TextEncoder {
    /// 模型配置
    config: ModelConfig,
    /// 是否已初始化
    initialized: Arc<RwLock<bool>>,
    /// 模型相关信息
    model_info: Arc<RwLock<Option<ModelInfo>>>,
}

/// 模型信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub version: String,
    pub embedding_dimension: usize,
    pub vocabulary_size: usize,
}

impl TextEncoder {
    /// 创建新的文本编码器
    pub fn new(config: ModelConfig) -> Self {
        Self {
            config,
            initialized: Arc::new(RwLock::new(false)),
            model_info: Arc::new(RwLock::new(None)),
        }
    }

    /// 初始化模型
    pub fn initialize(&self) -> Result<(), Box<dyn Error>> {
        let mut initialized = self.initialized.write().unwrap();
        
        if *initialized {
            return Ok(());
        }

        // 模拟模型初始化过程
        let model_info = ModelInfo {
            name: self.config.model_path.clone(),
            version: "1.0.0".to_string(),
            embedding_dimension: 384, // MiniLM模型的典型维度
            vocabulary_size: 30522,
        };

        let mut info_lock = self.model_info.write().unwrap();
        *info_lock = Some(model_info);
        
        *initialized = true;
        
        println!("TextEncoder initialized with model: {}", self.config.model_path);
        Ok(())
    }

    /// 编码单个文本
    pub fn encode_single(&self, text: &str) -> Result<Vec<f32>, Box<dyn Error>> {
        // 检查是否已初始化
        let initialized = self.initialized.read().unwrap();
        if !*initialized {
            return Err("Model not initialized. Call initialize() first.".into());
        }

        // 模拟文本编码过程
        // 在实际实现中，这里会调用真正的Sentence-BERT模型
        let embedding = self.simulate_encoding(text)?;
        
        Ok(embedding)
    }

    /// 批量编码文本
    pub fn encode_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>, Box<dyn Error>> {
        // 检查是否已初始化
        let initialized = self.initialized.read().unwrap();
        if !*initialized {
            return Err("Model not initialized. Call initialize() first.".into());
        }

        let mut embeddings = Vec::new();
        for text in texts {
            embeddings.push(self.encode_single(text)?);
        }

        Ok(embeddings)
    }

    /// 获取模型信息
    pub fn get_model_info(&self) -> Option<ModelInfo> {
        let info = self.model_info.read().unwrap();
        info.clone()
    }

    /// 模拟编码过程（在实际实现中会被替换为真正的模型推理）
    fn simulate_encoding(&self, text: &str) -> Result<Vec<f32>, Box<dyn Error>> {
        // 获取模型维度信息
        let info = self.model_info.read().unwrap();
        let embedding_dim = info.as_ref()
            .map(|info| info.embedding_dimension)
            .unwrap_or(384); // 默认维度

        // 生成确定性的模拟嵌入向量
        // 这里使用文本内容的哈希来生成伪随机向量
        let hash = self.text_hash(text);
        let mut embedding = Vec::with_capacity(embedding_dim);
        
        for i in 0..embedding_dim {
            // 使用哈希值和索引来生成伪随机浮点数
            let value = ((hash.wrapping_add(i as u64) as f32 * 0.1).sin() * 0.5) as f32;
            embedding.push(value);
        }

        // 归一化向量（L2范数）
        let norm = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 0.0 {
            for val in embedding.iter_mut() {
                *val /= norm;
            }
        }

        Ok(embedding)
    }

    /// 简单的文本哈希函数
    fn text_hash(&self, text: &str) -> u64 {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        text.hash(&mut hasher);
        hasher.finish()
    }

    /// 预热模型（加载到内存中）
    pub fn warm_up(&self, sample_texts: &[&str]) -> Result<(), Box<dyn Error>> {
        println!("Warming up model with {} sample texts...", sample_texts.len());
        
        for text in sample_texts {
            let _embedding = self.encode_single(text)?;
        }
        
        println!("Model warm-up completed.");
        Ok(())
    }
}

impl Drop for TextEncoder {
    fn drop(&mut self) {
        println!("TextEncoder is being dropped.");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_text_encoder_creation() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        
        assert!(!*encoder.initialized.read().unwrap());
    }

    #[test]
    fn test_model_initialization() {
        let config = ModelConfig {
            model_path: "test-model".to_string(),
            ..Default::default()
        };
        let encoder = TextEncoder::new(config);
        
        assert!(encoder.initialize().is_ok());
        assert!(*encoder.initialized.read().unwrap());
        
        let info = encoder.get_model_info().unwrap();
        assert_eq!(info.name, "test-model");
        assert_eq!(info.embedding_dimension, 384);
    }

    #[test]
    fn test_single_encoding() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let embedding = encoder.encode_single("Hello, world!").unwrap();
        assert_eq!(embedding.len(), 384); // 默认维度
        
        // 检查向量是否已归一化
        let norm: f32 = embedding.iter().map(|x| x * x).sum();
        assert!((norm - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_batch_encoding() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let texts = vec![
            "Hello, world!".to_string(),
            "Goodbye, world!".to_string(),
            "How are you?".to_string(),
        ];
        
        let embeddings = encoder.encode_batch(&texts).unwrap();
        assert_eq!(embeddings.len(), 3);
        assert_eq!(embeddings[0].len(), 384);
        assert_eq!(embeddings[1].len(), 384);
        assert_eq!(embeddings[2].len(), 384);
    }

    #[test]
    fn test_similar_texts_similarity() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let text1 = "Hello, world!";
        let text2 = "Hello, world!"; // 完全相同
        
        let emb1 = encoder.encode_single(text1).unwrap();
        let emb2 = encoder.encode_single(text2).unwrap();
        
        // 相同文本应该有相同的嵌入向量
        assert_eq!(emb1, emb2);
    }

    #[test]
    fn test_different_texts_dissimilarity() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let text1 = "Hello, world!";
        let text2 = "Completely different text.";
        
        let emb1 = encoder.encode_single(text1).unwrap();
        let emb2 = encoder.encode_single(text2).unwrap();
        
        // 不同文本应该有不同的嵌入向量
        assert_ne!(emb1, emb2);
    }
}