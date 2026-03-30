"""
Agent action endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user
from app.agents import get_agent
from app.utils.logger import logger

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/actions/{action_name}")
async def execute_agent_action(
    action_name: str,
    parameters: dict,
    current_user: dict = Depends(get_current_user),
):
    """Execute an agent action."""
    try:
        agent = await get_agent()

        # Execute action
        result = await agent.execute_action(action_name, parameters)

        logger.info(f"Agent action executed: {action_name}")

        return {
            "status": "success",
            "action": action_name,
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing agent action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing agent action",
        )


@router.get("/actions")
async def list_agent_actions(
    current_user: dict = Depends(get_current_user),
):
    """List available agent actions."""
    try:
        agent = await get_agent()

        actions = [
            {
                "name": action.name,
                "description": action.description,
                "parameters": action.parameters,
            }
            for action in agent.actions.values()
        ]

        return {"actions": actions}

    except Exception as e:
        logger.error(f"Error listing actions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing actions",
        )
