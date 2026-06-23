#!/usr/bin/env bash
# Day 3: kubectl 命令速查表
# 用法：bash day3_kubectl_cheatsheet.sh
# 提示：每条命令后都可以加 | tee -a day3_output.log 记录输出

set -e

echo "=== 1. 集群信息 ==="
kubectl version --client
kubectl cluster-info

echo -e "\n=== 2. 节点 ==="
kubectl get nodes -o wide

echo -e "\n=== 3. 命名空间 ==="
kubectl get ns

echo -e "\n=== 4. 应用 Pod ==="
kubectl apply -f day3_pod.yaml

echo -e "\n=== 5. 等待 Pod 就绪 ==="
kubectl wait --for=condition=Ready pod/my-pod --timeout=60s

echo -e "\n=== 6. 查看 Pod ==="
kubectl get pod my-pod -o wide
kubectl get pod my-pod --show-labels
kubectl describe pod my-pod

echo -e "\n=== 7. 日志 ==="
kubectl logs my-pod

echo -e "\n=== 8. 进入 Pod ==="
# kubectl exec -it my-pod -- sh
# 在 Pod 内：
#   env | grep MY_VAR
#   curl localhost:80
#   exit
echo "（手动执行：kubectl exec -it my-pod -- sh）"

echo -e "\n=== 9. 端口转发（测试完 Ctrl+C 退出）==="
# kubectl port-forward my-pod 8080:80
# 另开终端：curl http://localhost:8080
echo "（手动执行：kubectl port-forward my-pod 8080:80）"

echo -e "\n=== 10. 命名空间实验 ==="
kubectl create namespace dev --dry-run=client -o yaml
kubectl create namespace dev
kubectl get pods -n dev

echo -e "\n=== 11. 标签选择器 ==="
kubectl get pods -l app=demo
kubectl get pods -l env=dev

echo -e "\n=== 12. 清理 ==="
kubectl delete -f day3_pod.yaml
kubectl delete namespace dev

echo -e "\n✓ 完成！请把每条命令的输出截图或复制到 day3_output.log"