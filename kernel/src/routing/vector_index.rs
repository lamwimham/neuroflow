//! 向量索引管理
//! 
//! 管理Agent能力描述的向量索引，支持快速相似度搜索

use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use ndarray::Array2;
use serde::{Deserialize, Serialize};
use ndarray::s;

/// Agent元数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentMetadata {
    pub agent_id: String,
    pub name: String,
    pub description: String,
    pub skills: Vec<String>,
    pub capabilities: Vec<String>,
    pub embedding: Vec<f32>,
}

/// 向量索引
pub struct VectorIndex {
    /// Agent元数据存储
    agents: Arc<RwLock<HashMap<String, AgentMetadata>>>,
    /// 向量矩阵 (agents × dimensions)
    embeddings_matrix: Arc<RwLock<Array2<f32>>>,
    /// Agent ID到索引位置的映射
    id_to_index: Arc<RwLock<HashMap<String, usize>>>,
    /// 索引到Agent ID的映射
    index_to_id: Arc<RwLock<Vec<String>>>,
    /// 特征维度
    dimensions: usize,
}

impl VectorIndex {
    /// 创建新的向量索引
    pub fn new(dimensions: usize) -> Self {
        Self {
            agents: Arc::new(RwLock::new(HashMap::new())),
            embeddings_matrix: Arc::new(RwLock::new(Array2::zeros((0, dimensions)))),
            id_to_index: Arc::new(RwLock::new(HashMap::new())),
            index_to_id: Arc::new(RwLock::new(Vec::new())),
            dimensions,
        }
    }

    /// 添加Agent到索引
    pub fn add_agent(&self, metadata: AgentMetadata) -> Result<(), Box<dyn std::error::Error>> {
        let mut agents = self.agents.write().unwrap();
        let mut id_to_index = self.id_to_index.write().unwrap();
        let mut index_to_id = self.index_to_id.write().unwrap();
        let mut embeddings_matrix = self.embeddings_matrix.write().unwrap();

        // 检查维度是否匹配
        if metadata.embedding.len() != self.dimensions {
            return Err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                self.dimensions,
                metadata.embedding.len()
            ).into());
        }

        // 检查Agent是否已存在
        if agents.contains_key(&metadata.agent_id) {
            return Err(format!("Agent with ID {} already exists", metadata.agent_id).into());
        }

        // 添加到映射
        let index = index_to_id.len();
        agents.insert(metadata.agent_id.clone(), metadata.clone());
        id_to_index.insert(metadata.agent_id.clone(), index);
        index_to_id.push(metadata.agent_id.clone());

        // 扩展向量矩阵
        let mut new_matrix = Array2::zeros((index + 1, self.dimensions));
        if index > 0 {
            new_matrix.slice_mut(s![0..index, ..]).assign(&*embeddings_matrix);
        }
        new_matrix.row_mut(index).assign(&ndarray::Array1::from(metadata.embedding));

        *embeddings_matrix = new_matrix;

        Ok(())
    }

    /// 批量添加Agents
    pub fn add_agents(&self, metadata_list: Vec<AgentMetadata>) -> Result<(), Box<dyn std::error::Error>> {
        for metadata in metadata_list {
            self.add_agent(metadata)?;
        }
        Ok(())
    }

    /// 更新现有Agent
    pub fn update_agent(&self, metadata: AgentMetadata) -> Result<(), Box<dyn std::error::Error>> {
        let mut agents = self.agents.write().unwrap();
        let id_to_index = self.id_to_index.read().unwrap();

        // 检查Agent是否存在
        if !agents.contains_key(&metadata.agent_id) {
            return Err(format!("Agent with ID {} does not exist", metadata.agent_id).into());
        }

        // 检查维度是否匹配
        if metadata.embedding.len() != self.dimensions {
            return Err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                self.dimensions,
                metadata.embedding.len()
            ).into());
        }

        // 获取索引位置
        let index = *id_to_index.get(&metadata.agent_id).unwrap();

        // 更新Agent元数据
        agents.insert(metadata.agent_id.clone(), metadata.clone());

        // 更新向量矩阵
        let mut embeddings_matrix = self.embeddings_matrix.write().unwrap();
        embeddings_matrix.row_mut(index).assign(&ndarray::Array1::from(metadata.embedding));

        Ok(())
    }

    /// 移除Agent
    pub fn remove_agent(&self, agent_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        let mut agents = self.agents.write().unwrap();
        let mut id_to_index = self.id_to_index.write().unwrap();
        let mut index_to_id = self.index_to_id.write().unwrap();
        let mut embeddings_matrix = self.embeddings_matrix.write().unwrap();

        // 检查Agent是否存在
        if !agents.contains_key(agent_id) {
            return Err(format!("Agent with ID {} does not exist", agent_id).into());
        }

        // 获取要删除的索引
        let remove_index = *id_to_index.get(agent_id).unwrap();

        // 从映射中移除
        agents.remove(agent_id);
        id_to_index.remove(agent_id);

        // 重建索引映射和向量矩阵
        let mut new_index_to_id = Vec::new();
        let mut new_id_to_index = HashMap::new();
        let mut new_embeddings = Array2::zeros((0, self.dimensions));

        for (i, current_agent_id) in index_to_id.iter().enumerate() {
            if i != remove_index {
                let new_index = new_index_to_id.len();
                new_index_to_id.push(current_agent_id.clone());
                new_id_to_index.insert(current_agent_id.clone(), new_index);
            }
        }

        // 重新构建向量矩阵（跳过要删除的行）
        if !new_index_to_id.is_empty() {
            new_embeddings = Array2::zeros((new_index_to_id.len(), self.dimensions));
            let mut new_row = 0;
            for (i, _) in index_to_id.iter().enumerate() {
                if i != remove_index {
                    new_embeddings.row_mut(new_row).assign(&embeddings_matrix.row(i));
                    new_row += 1;
                }
            }
        }

        *index_to_id = new_index_to_id;
        *id_to_index = new_id_to_index;
        *embeddings_matrix = new_embeddings;

        Ok(())
    }

    /// 搜索最相似的Agents
    pub fn search_similar(
        &self,
        query_embedding: &[f32],
        k: usize,
        threshold: f32,
    ) -> Result<Vec<(String, f32)>, Box<dyn std::error::Error>> {
        if query_embedding.len() != self.dimensions {
            return Err(format!(
                "Query embedding dimension mismatch: expected {}, got {}",
                self.dimensions,
                query_embedding.len()
            ).into());
        }

        let embeddings_matrix = self.embeddings_matrix.read().unwrap();
        let index_to_id = self.index_to_id.read().unwrap();

        // 计算余弦相似度
        let query_array = ndarray::Array1::from(query_embedding.to_vec());
        let mut similarities = Vec::new();

        for i in 0..embeddings_matrix.nrows() {
            let agent_embedding = embeddings_matrix.row(i);
            let similarity = cosine_similarity(&query_array, &agent_embedding);
            
            if similarity >= threshold {
                let agent_id = index_to_id[i].clone();
                similarities.push((agent_id, similarity));
            }
        }

        // 按相似度排序
        similarities.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

        // 返回前k个结果
        Ok(similarities.into_iter().take(k).collect())
    }

    /// 获取Agent元数据
    pub fn get_agent_metadata(&self, agent_id: &str) -> Option<AgentMetadata> {
        let agents = self.agents.read().unwrap();
        agents.get(agent_id).cloned()
    }

    /// 获取所有Agent IDs
    pub fn get_all_agent_ids(&self) -> Vec<String> {
        let agents = self.agents.read().unwrap();
        agents.keys().cloned().collect()
    }

    /// 获取索引大小
    pub fn size(&self) -> usize {
        let agents = self.agents.read().unwrap();
        agents.len()
    }

    /// 获取特征维度
    pub fn dimensions(&self) -> usize {
        self.dimensions
    }
}

/// 计算余弦相似度
fn cosine_similarity(a: &ndarray::Array1<f32>, b: &ndarray::ArrayView1<f32>) -> f32 {
    let dot_product = a.dot(b);
    let norm_a = a.dot(a).sqrt();
    let norm_b = b.dot(b).sqrt();
    
    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }
    
    dot_product / (norm_a * norm_b)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vector_index_creation() {
        let index = VectorIndex::new(768);
        assert_eq!(index.dimensions(), 768);
        assert_eq!(index.size(), 0);
    }

    #[test]
    fn test_add_and_search_agent() {
        let index = VectorIndex::new(4);
        
        let metadata = AgentMetadata {
            agent_id: "test_agent".to_string(),
            name: "Test Agent".to_string(),
            description: "A test agent".to_string(),
            skills: vec!["test".to_string()],
            capabilities: vec!["test".to_string()],
            embedding: vec![0.1, 0.2, 0.3, 0.4],
        };
        
        index.add_agent(metadata).unwrap();
        assert_eq!(index.size(), 1);
        
        let results = index.search_similar(&[0.1, 0.2, 0.3, 0.4], 1, 0.0).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].0, "test_agent");
    }

    #[test]
    fn test_similarity_threshold() {
        let index = VectorIndex::new(4);
        
        let metadata = AgentMetadata {
            agent_id: "similar_agent".to_string(),
            name: "Similar Agent".to_string(),
            description: "A similar agent".to_string(),
            skills: vec!["similar".to_string()],
            capabilities: vec!["similar".to_string()],
            embedding: vec![1.0, 0.0, 0.0, 0.0],
        };
        
        index.add_agent(metadata).unwrap();
        
        // 高阈值，应该找不到相似项
        let results = index.search_similar(&[0.0, 1.0, 0.0, 0.0], 1, 0.9).unwrap();
        assert_eq!(results.len(), 0);
        
        // 低阈值，应该找到相似项
        let results = index.search_similar(&[1.0, 0.0, 0.0, 0.0], 1, 0.0).unwrap();
        assert_eq!(results.len(), 1);
    }

    #[test]
    fn test_update_agent() {
        let index = VectorIndex::new(4);
        
        let metadata = AgentMetadata {
            agent_id: "update_agent".to_string(),
            name: "Original Agent".to_string(),
            description: "Original description".to_string(),
            skills: vec!["original".to_string()],
            capabilities: vec!["original".to_string()],
            embedding: vec![0.1, 0.2, 0.3, 0.4],
        };
        
        index.add_agent(metadata).unwrap();
        
        let updated_metadata = AgentMetadata {
            agent_id: "update_agent".to_string(),
            name: "Updated Agent".to_string(),
            description: "Updated description".to_string(),
            skills: vec!["updated".to_string()],
            capabilities: vec!["updated".to_string()],
            embedding: vec![0.5, 0.6, 0.7, 0.8],
        };
        
        index.update_agent(updated_metadata).unwrap();
        
        let results = index.search_similar(&[0.5, 0.6, 0.7, 0.8], 1, 0.0).unwrap();
        assert_eq!(results[0].0, "update_agent");
    }
}